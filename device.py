# -*- coding: utf-8 -*-
"""เชื่อมต่อบอร์ดจริงผ่าน USB และโหมดจำลองสำหรับห้องเรียนที่ไม่มีบอร์ด

ต้องติดตั้ง:  pip install mpremote pyserial
"""
import os
import random
import re
import subprocess
import sys
import tempfile
import threading

LINE_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*[:=]\s*(-?\d+(?:\.\d+)?)")


def parse_line(line):
    """อ่านบรรทัด เช่น 'distance_cm: 12.5' คืนค่า {'distance_cm': 12.5}"""
    m = LINE_RE.match(line)
    return {m.group(1): float(m.group(2))} if m else {}


def list_ports():
    try:
        from serial.tools import list_ports as lp
        return [(p.device, p.description) for p in lp.comports()]
    except Exception:
        return []


def has_mpremote():
    try:
        import mpremote  # noqa: F401
        return True
    except Exception:
        return False


class BoardLink:
    """รันและอัปโหลดโค้ด MicroPython ด้วย mpremote แล้วส่งผลลัพธ์กลับทีละบรรทัด"""

    def __init__(self):
        self.proc = None
        self.serial = None
        self._stop = threading.Event()

    def _tmp(self, code):
        fd, path = tempfile.mkstemp(suffix=".py", prefix="main_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(code)
        return path

    def _stream(self, args, on_line, on_done):
        def work():
            try:
                self.proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                             text=True, encoding="utf-8", errors="replace", bufsize=1)
                for line in self.proc.stdout:
                    on_line(line.rstrip("\r\n"))
                code = self.proc.wait()
                on_done(code)
            except FileNotFoundError:
                on_line("ไม่พบ mpremote กรุณาติดตั้งด้วยคำสั่ง: pip install mpremote")
                on_done(-1)
            except Exception as e:  # noqa: BLE001
                on_line("เกิดข้อผิดพลาด: %s" % e)
                on_done(-1)
            finally:
                self.proc = None
        threading.Thread(target=work, daemon=True).start()

    def run(self, port, code, on_line, on_done):
        """รันโค้ดบนบอร์ดทันทีโดยไม่บันทึกลงบอร์ด (ปิดโปรแกรมแล้วโค้ดหาย)"""
        self.stop()
        path = self._tmp(code)
        self._stream([sys.executable, "-m", "mpremote", "connect", port, "run", path], on_line, on_done)

    def upload(self, port, code, on_line, on_done):
        """บันทึกเป็น main.py บนบอร์ด เปิดบอร์ดครั้งต่อไปจะทำงานเอง"""
        self.stop()
        path = self._tmp(code)
        self._stream([sys.executable, "-m", "mpremote", "connect", port, "fs", "cp", path, ":main.py",
                      "+", "reset"], on_line, on_done)

    def exec_code(self, port, code, timeout=25):
        """รันโค้ดสั้น ๆ บนบอร์ดแล้วรอผล (ใช้ตรวจบอร์ดและตรวจการต่อสาย) คืนค่า (สำเร็จ, ข้อความ)"""
        self.stop()
        path = self._tmp(code)
        try:
            p = subprocess.run([sys.executable, "-m", "mpremote", "connect", port, "run", path],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
            return p.returncode == 0, (p.stdout or "") + (p.stderr or "")
        except subprocess.TimeoutExpired:
            return False, "บอร์ดไม่ตอบกลับภายใน %d วินาที" % timeout
        except FileNotFoundError:
            return False, "ไม่พบ mpremote กรุณาติดตั้งด้วยคำสั่ง: pip install mpremote"
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

    def install_lib(self, port, lib, on_line, on_done):
        self.stop()
        self._stream([sys.executable, "-m", "mpremote", "connect", port, "mip", "install", lib], on_line, on_done)

    def monitor(self, port, on_line, baud=115200):
        """อ่านข้อความจากบอร์ดผ่าน Serial หลังอัปโหลด (ใช้ pyserial)"""
        self.stop()
        try:
            import serial
        except ImportError:
            on_line("ไม่พบ pyserial กรุณาติดตั้งด้วยคำสั่ง: pip install pyserial")
            return
        self._stop.clear()

        def work():
            try:
                self.serial = serial.Serial(port, baud, timeout=0.5)
                while not self._stop.is_set():
                    raw = self.serial.readline()
                    if raw:
                        on_line(raw.decode("utf-8", "replace").rstrip("\r\n"))
            except Exception as e:  # noqa: BLE001
                on_line("เปิดพอร์ตไม่ได้: %s" % e)
            finally:
                if self.serial:
                    self.serial.close()
                self.serial = None
        threading.Thread(target=work, daemon=True).start()

    def stop(self):
        was_open = self.serial is not None
        self._stop.set()
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except Exception:  # noqa: BLE001
                pass
        if was_open:
            import time
            time.sleep(0.8)          # รอให้พอร์ต Serial ปิดก่อนเปิดใช้งานใหม่


class Simulator:
    """สร้างค่าจำลองของเซนเซอร์ และคำนวณสถานะอุปกรณ์ตามเงื่อนไข ใช้สอนเมื่อไม่มีบอร์ดจริง"""

    def __init__(self, result, kb):
        self.result = result
        self.values = {}
        self.ranges = {}
        for c in result.components:
            if c.get("type") == "sensor":
                lo, hi, kind = c.get("sim", [0, 100, "float"])
                for k in c.get("keys", []):
                    self.ranges[k] = (lo, hi, kind)
                    self.values[k] = (lo + hi) / 2 if kind != "bool" else 0

    def step(self):
        self.t = getattr(self, "t", 0) + 1
        rule = self.result.rule
        for k, (lo, hi, kind) in self.ranges.items():
            span = hi - lo
            if kind == "bool":
                if rule and rule["key"] == k:
                    self.values[k] = 1 if (self.t // 7) % 2 else 0   # สลับทุก ~5 วินาที
                elif random.random() < 0.12:
                    self.values[k] = 1 - self.values[k]
                continue
            if rule and rule["key"] == k:
                # สลับเป้าหมายให้ค่าข้ามเส้นเงื่อนไขเป็นระยะ นักเรียนจะเห็นอุปกรณ์เปิดและปิด
                below = (self.t // 9) % 2 == 1
                thr = rule["thr"]
                target = thr - span * 0.15 if below else thr + span * 0.25
                target = max(lo + span * 0.05, min(hi - span * 0.05, target))
                v = self.values[k] + (target - self.values[k]) * 0.35 + random.uniform(-0.03, 0.03) * span
            else:
                v = self.values[k] + random.uniform(-0.12, 0.12) * span
            self.values[k] = round(max(lo, min(hi, v)), 1)
        return dict(self.values)

    def actuator_states(self, values):
        return evaluate_rule(self.result.rule, values, [c["id"] for c in self.result.components if c.get("type") == "actuator"])


def evaluate_rule(rule, values, actuator_ids):
    if not rule:
        return {}
    v = values.get(rule["key"])
    if v is None:
        return {}
    thr = rule["thr"]
    ok = {"<": v < thr, "<=": v <= thr, ">": v > thr, ">=": v >= thr, "==": v == thr}.get(rule["op"], False)
    if rule["key"] in ("distance_cm", "distance_mm", "ir_distance_cm") and v <= 0:
        ok = False
    return {a: ok for a in rule.get("actuators", actuator_ids)}


# ---------------------------------------------------------------- ตรวจบอร์ดที่ต่ออยู่
DETECT_SCRIPT = """
import sys, os, gc
u = os.uname()
print("MP:", sys.implementation.name, ".".join(str(x) for x in sys.implementation.version[:3]))
print("MACHINE:", u.machine)
gc.collect()
print("FREE:", gc.mem_free())
print("FILES:", ",".join(os.listdir()))
try:
    from machine import Pin
    try:
        from machine import SoftI2C as I2Cx
    except ImportError:
        from machine import I2C as I2Cx
    m = u.machine.upper()
    if "S3" in m:
        pairs = ((8, 9), (11, 12))
    elif "C3" in m:
        pairs = ((8, 9),)
    elif "ESP32" in m:
        pairs = ((21, 22),)           # ห้ามสแกน GPIO 6-11 ของ ESP32 เพราะต่อกับแฟลช
    elif "ESP8266" in m:
        pairs = ((4, 5),)
    elif "RP2" in m or "PICO" in m:
        pairs = ((4, 5), (12, 13))
    else:
        pairs = ()
    for sda, scl in pairs:
        try:
            found = I2Cx(sda=Pin(sda), scl=Pin(scl), freq=100000).scan()
            if found:
                print("I2C:%d,%d:%s" % (sda, scl, ",".join(str(a) for a in found)))
        except Exception:
            pass
except Exception as e:
    print("I2CERR:", e)
"""

I2C_KNOWN = {0x3C: "oled", 0x3D: "oled", 0x68: "mpu6050", 0x69: "mpu6050", 0x76: "bmp280", 0x77: "bmp280",
             0x27: "lcd1602", 0x3F: "lcd1602", 0x29: "vl53l0x", 0x5A: "mlx90614", 0x57: "max30102"}


def guess_board(machine):
    m = machine.lower()
    for key, bid in (("nano esp32", "nano-esp32"), ("nano rp2040", "nano-rp2040"), ("esp32s3", "esp32-s3"),
                     ("esp32-s3", "esp32-s3"), ("esp32c3", "esp32-c3"), ("esp32-c3", "esp32-c3"),
                     ("esp32", "esp32-devkit"), ("esp8266", "esp8266-nodemcu"), ("pico", "pico"),
                     ("rp2040", "pico"), ("rp2350", "pico")):
        if key in m:
            return bid
    return None


def parse_detect(output):
    info = dict(mp=None, machine="", free=None, files=[], i2c=[], board_id=None)
    for line in output.splitlines():
        if line.startswith("MP:"):
            info["mp"] = line[3:].strip()
        elif line.startswith("MACHINE:"):
            info["machine"] = line[8:].strip()
        elif line.startswith("FREE:"):
            info["free"] = line[5:].strip()
        elif line.startswith("FILES:"):
            info["files"] = [f for f in line[6:].strip().split(",") if f]
        elif line.startswith("I2C:"):
            _, pins, addrs = line.split(":", 2)
            for a in addrs.split(","):
                if a.strip().isdigit():
                    a = int(a)
                    if not any(d["addr"] == a for d in info["i2c"]):
                        info["i2c"].append(dict(addr=a, pins=pins, comp=I2C_KNOWN.get(a)))
    info["board_id"] = guess_board(info["machine"])
    return info


FRIENDLY = [
    (r"no module named '?(\w+)", "ยังไม่ได้ติดตั้งไลบรารี {0} บนบอร์ด กดปุ่ม \"ติดตั้งไลบรารี\" ในแท็บสร้างโค้ด"),
    (r"ETIMEDOUT|Errno 116|Errno 110", "อุปกรณ์ไม่ตอบกลับ ตรวจสายสัญญาณและไฟเลี้ยง"),
    (r"ENODEV|Errno 19", "ไม่พบอุปกรณ์บนสาย I2C ตรวจสาย SDA SCL"),
    (r"invalid pin", "บอร์ดนี้ไม่มีขาที่เลือก เปลี่ยนรุ่นบอร์ดให้ตรงกับของจริง"),
    (r"could not (open|enter raw repl)|failed to access|Access is denied|PermissionError",
     "เปิดพอร์ต USB ไม่ได้ ปิดโปรแกรมอื่นที่ใช้พอร์ตอยู่ (Thonny, Arduino IDE) แล้วลองใหม่"),
]


def friendly(msg):
    for pat, text in FRIENDLY:
        m = re.search(pat, msg, re.I)
        if m:
            return text.format(*(g for g in m.groups() if g)) if m.groups() else text
    return msg


def parse_test(output):
    """อ่านผลตรวจสาย คืนค่า (สถานะ, ข้อความ) สถานะ = ok / fail / ask"""
    status, msg, values = None, "", []
    for line in output.splitlines():
        if line.startswith("TEST_OK"):
            status, msg = "ok", line[7:].strip()
        elif line.startswith("TEST_FAIL"):
            status, msg = "fail", line[9:].strip()
        elif line.startswith("TEST_ASK"):
            status, msg = "ask", line[8:].strip()
        elif line.startswith("VALUE:"):
            values.append(line[6:].strip())
    if status is None:
        lines = [l for l in output.strip().splitlines() if l.strip()]
        status, msg = "fail", (lines[-1] if lines else "บอร์ดไม่ตอบกลับ")
    msg = friendly(msg)
    if values:
        msg = (msg + " | ค่าที่อ่านได้: " + ", ".join(values[-3:])).strip(" |")
    return status, msg

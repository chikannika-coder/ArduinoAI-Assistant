# -*- coding: utf-8 -*-
"""ทดสอบคลังตัวอย่าง Arduino -> MicroPython และคู่มือคำสั่ง: python test_examples.py

1) ปรับขาให้ทุกบอร์ดที่รัน MicroPython ได้ ต้องไม่มีข้อผิดพลาด
2) รันโค้ดจริงบนบอร์ดจำลอง (machine จำลอง) ไม่กี่รอบ ต้องไม่ Error
3) คู่มือคำสั่ง Arduino ต้องโหลดได้ และโค้ด MicroPython ในคู่มือต้องไวยากรณ์ถูก
"""
import os
import sys
import time as _time
import types

from kb import KnowledgeBase
from generator import CodeGenerator, check_code
import examples_lib


# ------------------------------------------------------------ บอร์ดจำลอง
class _Stop(Exception):
    pass


class Pin:
    IN, OUT, PULL_UP, PULL_DOWN, IRQ_RISING, IRQ_FALLING = 1, 2, 3, 4, 8, 16

    def __init__(self, pin, mode=None, pull=None, value=None):
        if not isinstance(pin, (int, str)):
            raise TypeError("bad pin %r" % (pin,))
        self.pin, self._v, self._in, self._n = pin, 1 if pull == Pin.PULL_UP else 0, mode == Pin.IN, 0

    def value(self, v=None):
        if v is None:
            if self._in:                   # ขาเข้า: จำลองการกด/ปล่อยปุ่มเป็นระยะ
                self._n += 1
                if self._n % 5 == 0:
                    self._v = 1 - self._v
            return self._v
        self._v = 1 if v else 0

    def on(self):
        self._v = 1

    def off(self):
        self._v = 0

    def irq(self, **kw):
        pass


class ADC:
    ATTN_11DB, ATTN_0DB = 3, 0
    _n = 0

    def __init__(self, pin):
        if not isinstance(pin, (Pin, int)):
            raise TypeError("ADC needs Pin or int")

    def read_u16(self):
        ADC._n += 7919
        return ADC._n % 65536


class ADC32(ADC):
    def atten(self, a):
        pass


class PWM:
    def __init__(self, pin, freq=None, duty_u16=None):
        if not isinstance(pin, Pin):
            raise TypeError("PWM needs Pin")

    def freq(self, f=None):
        if f is not None and not (0 < f < 40_000_000):
            raise ValueError("freq out of range: %r" % f)

    def duty_u16(self, d=None):
        if d is not None and not (0 <= d <= 65535):
            raise ValueError("duty out of range: %r" % d)

    def duty_ns(self, d):
        pass

    def deinit(self):
        pass


class I2C:
    def __init__(self, *a, **kw):
        pass

    def scan(self):
        return [0x3C]


def time_pulse_us(pin, level, timeout):
    return 580


class FakeTime(types.ModuleType):
    def __init__(self, limit):
        super().__init__("time")
        self.calls, self.limit, self.t = 0, limit, 0

    def _tick(self, ms):
        self.t += max(ms, 1)
        self.calls += 1
        if self.calls > self.limit:
            raise _Stop()

    def sleep(self, s):
        self._tick(int(s * 1000))

    def sleep_ms(self, ms):
        self._tick(ms)

    def sleep_us(self, us):
        self._tick(0)

    def ticks_ms(self):
        self._tick(0)
        return self.t

    def ticks_us(self):
        return self.ticks_ms() * 1000

    def ticks_diff(self, a, b):
        return a - b


class OLED:
    def __init__(self, *a):
        pass

    fill = text = show = lambda self, *a: None


class RTC:
    def datetime(self, *a):
        return (2026, 9, 28, 0, 8, 0, 0, 0)       # 8 โมงเช้า: ให้โค้ดที่ทำงานตามเวลาได้ลองทำงาน


class FakeDHT:
    def __init__(self, pin):
        if not isinstance(pin, Pin):
            raise TypeError("DHT needs Pin")
        self._n = 0

    def measure(self):
        self._n += 1
        if self._n % 7 == 0:                         # จำลองอ่านพลาดบางครั้ง (สายหลวม)
            raise OSError("ETIMEDOUT")

    def temperature(self):
        return 20 + self._n % 15

    def humidity(self):
        return 50 + self._n % 40


class FakeOneWire:
    def __init__(self, pin):
        if not isinstance(pin, Pin):
            raise TypeError("OneWire needs Pin")


class FakeDS:
    def __init__(self, ow):
        pass

    def scan(self):
        return [b"12345678"]

    def convert_temp(self):
        pass

    def read_temp(self, rom):
        return 27.5


class FakePoll:
    def register(self, *a):
        pass

    def poll(self, t=0):
        return []                                  # ไม่มีข้อมูลเข้าทาง USB


class FakeWLAN:
    def __init__(self, i):
        pass

    def active(self, *a):
        return True

    def connect(self, *a):
        pass

    def isconnected(self):
        return True

    def ifconfig(self):
        return ("192.168.1.50", "255.255.255.0", "192.168.1.1", "8.8.8.8")


class FakeSocket:
    def __init__(self, *a):
        self.n = 0

    def bind(self, addr):
        pass

    def settimeout(self, t):
        pass

    def recvfrom(self, n):
        self.n += 1
        if self.n % 5 == 0:                        # บางรอบมีคำสั่งเข้ามา
            return b"ALL:T45,I30,M60,R20,P90\nHB", ("192.168.1.10", 5000)
        raise OSError(110)

    def sendto(self, data, addr):
        pass


def run(code, family, tmpdir):
    machine = types.ModuleType("machine")
    machine.Pin, machine.PWM, machine.I2C, machine.time_pulse_us = Pin, PWM, I2C, time_pulse_us
    machine.ADC = ADC32 if family == "esp32" else ADC
    machine.RTC = RTC
    ssd = types.ModuleType("ssd1306")
    ssd.SSD1306_I2C = OLED
    dht_m = types.ModuleType("dht")
    dht_m.DHT11 = dht_m.DHT22 = FakeDHT
    ow = types.ModuleType("onewire")
    ow.OneWire = FakeOneWire
    dsm = types.ModuleType("ds18x20")
    dsm.DS18X20 = FakeDS
    sel = types.ModuleType("select")
    sel.POLLIN, sel.poll = 1, FakePoll
    net = types.ModuleType("network")
    net.STA_IF, net.AP_IF, net.WLAN = 0, 1, FakeWLAN
    sk = types.ModuleType("socket")
    sk.AF_INET, sk.SOCK_DGRAM, sk.SOCK_STREAM, sk.socket = 2, 2, 1, FakeSocket
    ft = FakeTime(400)
    names = ("machine", "time", "ssd1306", "dht", "onewire", "ds18x20", "select", "network", "socket")
    saved = {k: sys.modules.get(k) for k in names}
    sys.modules.update(machine=machine, time=ft, ssd1306=ssd, dht=dht_m, onewire=ow, ds18x20=dsm,
                       select=sel, network=net, socket=sk)
    cwd = os.getcwd()
    os.chdir(tmpdir)
    import contextlib
    import io
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(code, "main.py", "exec"), {"__name__": "__main__"})
    except _Stop:
        pass
    finally:
        os.chdir(cwd)
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    return ft.calls


if __name__ == "__main__":
    import tempfile
    kb = KnowledgeBase()
    gen = CodeGenerator(kb)
    boards = [b for b in kb.boards if b["micropython"] and b["family"] != "microbit"]
    bad = n = 0
    limited = []
    tmp = tempfile.mkdtemp()
    for e in examples_lib.load_index():
        if "py" not in e:
            continue
        with open(os.path.join(examples_lib.FOLDER, e["py"]), encoding="utf-8") as f:
            src = f.read()
        for b in boards:
            n += 1
            code, res, notes = examples_lib.adapt(src, gen, b)
            short = [x for x in res.errors + notes if "ไม่พอ" in x or "ไม่มีขาว่าง" in x]
            if short:                      # บอร์ดมีขาน้อยเกินไป: โปรแกรมต้องแจ้งเตือน (เป็นข้อจำกัดของบอร์ด ไม่ใช่บั๊ก)
                limited.append("%s @ %s" % (e["id"].split("/")[-1], b["id"]))
                continue
            errs = res.errors + notes + check_code(code, b)[0]
            try:
                run(code, b["family"], tmp)
            except Exception as ex:  # noqa: BLE001
                errs.append("รันไม่ผ่าน: %r" % ex)
            if errs:
                bad += 1
                print("ตัวอย่างมีปัญหา:", e["id"], b["id"], errs)
    print("examples-ok:", n - bad - len(limited), "/", n - len(limited))
    print("ขาไม่พอ (โปรแกรมแจ้งเตือนแล้ว):", len(limited), "กรณี:", ", ".join(limited))

    # ---- คู่มือคำสั่ง
    ref = kb.reference()
    bad = 0
    for r in ref:
        if r.get("micropython"):
            try:
                compile(r["micropython"], r["id"], "exec")
            except SyntaxError as ex:
                bad += 1
                print("โค้ดในคู่มือผิด:", r["id"], ex)
    print("reference-ok:", sum(1 for r in ref if r.get("micropython")) - bad, "/", sum(1 for r in ref if r.get("micropython")),
          "| ทั้งหมด", len(ref), "หน้า")

    # ---- วิเคราะห์โค้ด Arduino แบบไม่ใช้ AI กับตัวอย่างทุกไฟล์ในคลัง
    from analyzer import offline_analyze
    tested = ok = 0
    for e in examples_lib.load_index():
        with open(os.path.join(examples_lib.FOLDER, e["ino"]), encoding="utf-8", errors="replace") as f:
            comp, _ = offline_analyze(f.read(), kb)
        if comp["type"] == "info":
            continue
        tested += 1
        k2 = KnowledgeBase()
        k2.components = [c for c in k2.components if c["id"] != comp["id"]] + [comp]
        k2.reindex()
        g2 = CodeGenerator(k2)
        b = k2.board_by_id["esp32-devkit"]
        r = g2.generate(("อ่าน " if comp["type"] == "sensor" else "") + comp["keywords"][0], b["id"])
        errs = r.errors + check_code(r.code, b)[0]
        if errs:
            print("วิเคราะห์โค้ดแล้วสร้างโค้ดไม่ผ่าน:", e["id"], errs)
        else:
            ok += 1
    print("analyzer-ok:", ok, "/", tested)

    # ---- กฎขาของ Arduino ตามผังขาจริง (Arduino IDE 1.6.0)
    CASES = [
        ("arduino-leonardo", "แสดงบนจอ OLED ให้ LED ติด", lambda r: ("D2", "D3") == tuple(
            w["board_pin"] for w in r.wiring if w["comp"] == "oled" and w["kind"] == "signal") and not r.errors),
        ("arduino-leonardo", "แสดงบนจอ OLED ให้ LED ขา 2 ติด", lambda r: any("I2C" in x for x in r.errors)),
        ("arduino-nano", "อ่านค่าแสง LDR ขา A7", lambda r: not r.errors),
        ("arduino-nano", "ให้ LED ขา A6 กระพริบ", lambda r: any("แอนะล็อกได้อย่างเดียว" in x for x in r.errors)),
        ("arduino-uno", "ให้ LED ขา 20 กระพริบ", lambda r: any("ไม่มีขา" in x for x in r.errors)),
        ("arduino-mega", "อ่านค่าแสง LDR ขา A12 ถ้ามืดให้ LED ขา 30 ติด", lambda r: not r.errors and "A12" in r.code),
    ]
    ok = 0
    for bid, cmd, check in CASES:
        r = gen.generate(cmd, bid)
        if check(r):
            ok += 1
        else:
            print("กฎขา Arduino ไม่ผ่าน:", bid, cmd, r.errors, [(w["comp"], w["board_pin"]) for w in r.wiring])
    print("avr-pin-rules-ok:", ok, "/", len(CASES))

    # ---- ตัวตรวจโค้ด (2.5): โค้ดต้นฉบับเครื่องผสมปุ๋ยใช้ขา 2-5 ซ้ำกับจอ LCD ต้องเจอ 4 จุด และตัวอย่าง Arduino IDE ต้องไม่ฟ้องผิด
    import glob
    import lint
    fm = open(os.path.join(examples_lib.FOLDER, "16.Farm/FertilizerMixer/FertilizerMixer.ino"), encoding="utf-8").read()
    ok_fm = len(lint.check(fm)[0]) == 4
    false_err = [p for p in glob.glob(os.path.join(examples_lib.FOLDER, "*", "*", "*.ino"))
                 if "FertilizerMixer" not in p and lint.check(open(p, encoding="utf-8", errors="replace").read())[0]]
    for p in false_err:
        print("ตัวตรวจโค้ดฟ้องผิด:", p, lint.check(open(p, encoding="utf-8", errors="replace").read())[0])
    print("lint-ok:", "ผ่าน" if ok_fm and not false_err else "ไม่ผ่าน")

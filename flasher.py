# -*- coding: utf-8 -*-
"""ลง MicroPython ให้บอร์ด (ทำครั้งเดียวต่อบอร์ด)

ESP32 / ESP32-S3 / ESP32-C3 / ESP8266 → ดาวน์โหลดไฟล์ .bin แล้วเขียนด้วย esptool
Raspberry Pi Pico / Pico 2            → ดาวน์โหลดไฟล์ .uf2 แล้วคัดลอกลงไดรฟ์ RPI-RP2 ให้เอง

ไฟล์เฟิร์มแวร์ที่ดาวน์โหลดแล้วเก็บไว้ในโฟลเดอร์ firmware/ ครูคัดลอกโฟลเดอร์นี้
ไปเครื่องอื่นได้ ห้องเรียนที่ไม่มีอินเทอร์เน็ตจะใช้ไฟล์ในโฟลเดอร์นี้แทน
ต้องติดตั้ง:  pip install esptool
"""
import codecs
import glob
import os
import queue
import re
import shutil
import string
import subprocess
import sys
import threading
import time
import urllib.request
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from kb import BASE

FW_DIR = os.path.join(BASE, "firmware")
SITE = "https://micropython.org"
FALLBACK = "20260824-v1.29.0"      # รุ่นล่าสุดที่ตรวจแล้ว ใช้เมื่ออ่านหน้าดาวน์โหลดไม่ได้
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

_ESP32 = dict(kind="esp", chip="esp32", offset="0x1000", variants=[("ESP32 ทั่วไป", "ESP32_GENERIC", "ESP32_GENERIC")])
PROFILES = {
    "esp32-devkit": _ESP32,
    "kidbright32": dict(_ESP32, note="KidBright32 ใช้ชิป ESP32 จึงใช้เฟิร์มแวร์ ESP32 ทั่วไป "
                                     "หลังลงแล้ว โปรแกรม KidBright IDE จะใช้กับบอร์ดนี้ไม่ได้จนกว่าจะลงเฟิร์มแวร์ของ KidBright กลับ"),
    "esp32-cam": dict(_ESP32, variants=[("ESP32 มี PSRAM (ESP32-CAM)", "ESP32_GENERIC-SPIRAM", "ESP32_GENERIC")],
                      note="ESP32-CAM ไม่มีปุ่ม BOOT บนบอร์ด ถ้าใช้บอร์ดเสริม ESP32-CAM-MB ให้กดปุ่ม IO0 บนบอร์ดเสริมแทน "
                           "ถ้าใช้ USB-TTL ให้ต่อสาย GPIO0 ลง GND ก่อนเสียบไฟ แล้วถอดสายนี้ออกเมื่อลงเสร็จ"),
    "esp32-s3": dict(kind="esp", chip="esp32s3", offset="0x0",
                     variants=[("ESP32-S3 ทั่วไป", "ESP32_GENERIC_S3", "ESP32_GENERIC_S3"),
                               ("ESP32-S3 มี PSRAM แบบ Octal (บนชิปเขียนว่า N8R8 / N16R8)",
                                "ESP32_GENERIC_S3-SPIRAM_OCT", "ESP32_GENERIC_S3")],
                     note="ถ้าบอร์ดมีช่อง USB 2 ช่อง ให้เสียบช่องที่เขียนว่า USB หรือ COM ก็ได้ "
                          "ถ้าหาบอร์ดไม่เจอ: ถอดสาย กด BOOT ค้าง เสียบสาย แล้วปล่อย จากนั้นกด 'ค้นหาพอร์ต' ใหม่"),
    "esp32-c3": dict(kind="esp", chip="esp32c3", offset="0x0",
                     variants=[("ESP32-C3", "ESP32_GENERIC_C3", "ESP32_GENERIC_C3")],
                     note="บอร์ด C3 SuperMini: ถ้าหาบอร์ดไม่เจอ ให้ถอดสาย กด BOOT ค้าง เสียบสาย แล้วปล่อย "
                          "จากนั้นกด 'ค้นหาพอร์ต' ใหม่ หลังลงเสร็จให้กดปุ่ม RST 1 ครั้ง"),
    "esp8266-nodemcu": dict(kind="esp", chip="esp8266", offset="0x0",
                            variants=[("ESP8266 (NodeMCU / Wemos D1 mini)", "ESP8266_GENERIC", "ESP8266_GENERIC")],
                            note="บอร์ด NodeMCU และ Wemos D1 mini ส่วนใหญ่เข้าโหมดลงเฟิร์มแวร์เองได้ ถ้าไม่ได้ให้กดปุ่ม FLASH แทนปุ่ม BOOT"),
    "pico": dict(kind="uf2", variants=[("Raspberry Pi Pico", "RPI_PICO", "RPI_PICO"),
                                       ("Raspberry Pi Pico W (มี Wi-Fi)", "RPI_PICO_W", "RPI_PICO_W"),
                                       ("Raspberry Pi Pico 2", "RPI_PICO2", "RPI_PICO2"),
                                       ("Raspberry Pi Pico 2 W (มี Wi-Fi)", "RPI_PICO2_W", "RPI_PICO2_W")],
                 note="ดูรุ่นได้ที่ตัวบอร์ด: Pico W มีกล่องโลหะสี่เหลี่ยม (ชิป Wi-Fi) ข้างปุ่ม BOOTSEL "
                      "Pico 2 มีตัวเลข 2 บนบอร์ดและชิปเขียนว่า RP2350"),
}
NOT_SUPPORTED = {
    "nano-esp32": "Arduino Nano ESP32 ใช้วิธีลงเฟิร์มแวร์แบบเฉพาะ ให้ใช้โปรแกรม Arduino MicroPython Installer (labs.arduino.cc)",
    "nano-rp2040": "Arduino Nano RP2040 Connect ใช้เฟิร์มแวร์เฉพาะของ Arduino ให้ใช้โปรแกรม Arduino MicroPython Installer (labs.arduino.cc)",
    "microbit-v2": "micro:bit ไม่ต้องลงเฟิร์มแวร์เอง ให้เขียนโค้ดที่ python.microbit.org แล้วกดส่งลงบอร์ดจากหน้าเว็บ",
}
CHIP_TO_BOARD = {"ESP32": "esp32-devkit", "ESP32-S3": "esp32-s3", "ESP32-C3": "esp32-c3", "ESP8266": "esp8266-nodemcu"}

BOOT_HOW = ("วิธีเข้าโหมดลงเฟิร์มแวร์:\n"
            "1. กดปุ่ม BOOT บนบอร์ดค้างไว้ (บางบอร์ดเขียนว่า IO0 หรือ FLASH)\n"
            "2. กดปุ่ม EN (หรือ RST) 1 ครั้งแล้วปล่อย โดยยังกด BOOT ค้างอยู่\n"
            "3. ปล่อยปุ่ม BOOT แล้วกด \"ลองอีกครั้ง\" ทันที\n"
            "หรือกด \"ลองอีกครั้ง\" แล้วกด BOOT ค้างไว้ตอนที่ข้อความเปลี่ยนเป็นสีส้ม\n"
            "ถ้ายังไม่ได้ ลองเปลี่ยนสาย USB (ต้องเป็นสายที่ส่งข้อมูลได้) หรือเสียบช่อง USB อื่นของคอมพิวเตอร์")

DIAG = [
    ("noesptool", r"No module named '?esptool",
     "ยังไม่ได้ติดตั้ง esptool กดปุ่มเริ่มอีกครั้ง โปรแกรมจะถามเพื่อติดตั้งให้"),
    ("noport", r"could not open port.*(FileNotFound|cannot find|No such file)",
     "ไม่พบพอร์ตนี้ บอร์ดอาจหลุด หรือเลขพอร์ตเปลี่ยน\nเสียบสายใหม่ กด 'ค้นหาพอร์ต' ที่หน้าหลัก แล้วลองอีกครั้ง"),
    ("port", r"could not open port|PermissionError|Access is denied|port is busy|being used",
     "พอร์ตนี้ถูกโปรแกรมอื่นใช้อยู่\nปิด Thonny, Arduino IDE และ Serial Monitor ทุกหน้าต่าง แล้วลองอีกครั้ง"),
    ("wrongchip", r"This chip is (ESP[\w-]+),? not (ESP[\w-]+)", ""),
    ("boot", r"Wrong boot mode|Failed to connect|No serial data received|Invalid head of packet",
     "บอร์ดยังไม่เข้าโหมดลงเฟิร์มแวร์\n\n" + BOOT_HOW),
    ("slow", r"timed out|Packet content transfer stopped|Serial data stream stopped|checksum|corrupt|MD5 of file",
     "การส่งข้อมูลขาดหาย ลองเปลี่ยนสาย USB ให้สั้นลง หรือเสียบช่อง USB ด้านหลังเครื่อง แล้วลองอีกครั้ง"),
]


def diagnose(text):
    for kind, pat, msg in DIAG:
        m = re.search(pat, text, re.I)
        if m:
            return kind, msg, m
    lines = [l for l in text.strip().splitlines() if l.strip()]
    return "other", "ลงเฟิร์มแวร์ไม่สำเร็จ\n" + (lines[-1] if lines else ""), None


# ---------------------------------------------------------------- เฟิร์มแวร์
def _ext(profile):
    return "uf2" if profile["kind"] == "uf2" else "bin"


def _name_re(prefix, ext):
    # ESP32_GENERIC ต้องไม่จับ ESP32_GENERIC_S3 หรือ ESP32_GENERIC-SPIRAM และไม่เอารุ่นทดลอง (preview)
    return re.compile(r"%s-(\d{8})-v(\d+)\.(\d+)(?:\.(\d+))?\.%s$" % (re.escape(prefix), ext))


def _version_key(m):
    return int(m.group(2)), int(m.group(3)), int(m.group(4) or 0), m.group(1)


def cached_firmware(prefix, ext):
    """ไฟล์รุ่นใหม่สุดที่อยู่ในโฟลเดอร์ firmware/ แล้ว"""
    pat = _name_re(prefix, ext)
    found = [(pat.match(os.path.basename(p)), p) for p in glob.glob(os.path.join(FW_DIR, "*." + ext))]
    found = [(m, p) for m, p in found if m]
    return max(found, key=lambda x: _version_key(x[0]))[1] if found else None


def _open(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ArduinoAI-Assistant"})
    return urllib.request.urlopen(req, timeout=timeout)


def latest_url(prefix, page, ext):
    """อ่านหน้าดาวน์โหลดของ micropython.org แล้วหาไฟล์รุ่นเสถียรล่าสุด คืน None ถ้าอ่านไม่ได้"""
    html = _open("%s/download/%s/" % (SITE, page)).read().decode("utf-8", "replace")
    pat = re.compile(r"/resources/firmware/(%s-\d{8}-v\d+\.\d+(?:\.\d+)?\.%s)" % (re.escape(prefix), ext))
    names = {m.group(1) for m in pat.finditer(html)}
    best = [(_name_re(prefix, ext).match(n), n) for n in names]
    best = [(m, n) for m, n in best if m]
    if not best:
        return None
    return "%s/resources/firmware/%s" % (SITE, max(best, key=lambda x: _version_key(x[0]))[1])


def download(url, progress):
    os.makedirs(FW_DIR, exist_ok=True)
    dest = os.path.join(FW_DIR, url.rsplit("/", 1)[1])
    if os.path.exists(dest) and os.path.getsize(dest) > 100000:
        return dest
    tmp = dest + ".part"
    with _open(url, timeout=30) as r, open(tmp, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        got = 0
        while True:
            chunk = r.read(65536)
            if not chunk:
                break
            f.write(chunk)
            got += len(chunk)
            if total:
                progress(got * 100.0 / total)
    if os.path.getsize(tmp) < 100000:
        os.remove(tmp)
        raise IOError("ไฟล์ที่ดาวน์โหลดเล็กผิดปกติ")
    os.replace(tmp, dest)
    return dest


def get_firmware(prefix, page, ext, log, progress):
    """หาเฟิร์มแวร์: รุ่นล่าสุดจากเว็บ → ถ้าไม่มีเน็ตใช้ไฟล์ในโฟลเดอร์ firmware/ → ถ้าไม่มีเลยจึงแจ้งข้อผิดพลาด"""
    ext_cached = cached_firmware(prefix, ext)
    try:
        url = latest_url(prefix, page, ext)
    except Exception as e:  # noqa: BLE001
        log("อ่านหน้าดาวน์โหลดไม่ได้ (%s)" % e)
        url = None
    if url is None and ext_cached:
        log("ใช้ไฟล์ที่เคยดาวน์โหลดไว้: " + os.path.basename(ext_cached))
        return ext_cached
    url = url or "%s/resources/firmware/%s-%s.%s" % (SITE, prefix, FALLBACK, ext)
    log("ดาวน์โหลด " + url)
    try:
        return download(url, progress)
    except Exception as e:  # noqa: BLE001
        if ext_cached:
            log("ดาวน์โหลดไม่ได้ (%s) ใช้ไฟล์เดิม: %s" % (e, os.path.basename(ext_cached)))
            return ext_cached
        raise IOError("ดาวน์โหลดเฟิร์มแวร์ไม่ได้ (%s)\nตรวจอินเทอร์เน็ต หรือดาวน์โหลดเองจาก %s/download/%s/ "
                      "แล้วกด 'ใช้ไฟล์ในเครื่อง'" % (e, SITE, page))


# ---------------------------------------------------------------- esptool
def esptool_version():
    try:
        import esptool
        return tuple(int(x) for x in re.findall(r"\d+", esptool.__version__)[:2])
    except Exception:  # noqa: BLE001
        return None


def esptool_cmd(chip, port, baud, offset, path, version):
    # esptool 5 เปลี่ยนชื่อคำสั่งเป็นแบบขีด (write-flash) รุ่น 4 ใช้ขีดล่าง
    write = "write-flash" if version and version[0] >= 5 else "write_flash"
    # --erase-all ล้างข้อมูลเก่าในคำสั่งเดียวกัน นักเรียนจึงกด BOOT แค่ครั้งเดียว
    return [sys.executable, "-u", "-m", "esptool", "--chip", chip, "--port", port, "--baud", str(baud),
            write, "-z", "--erase-all", offset, path]


def _popen(cmd):
    env = dict(os.environ, PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, creationflags=flags)


def stream(proc, on_line, on_partial):
    """อ่านผลทีละตัวอักษร เพราะ esptool พิมพ์ 'Connecting....' ต่อกันโดยไม่ขึ้นบรรทัดใหม่"""
    dec = codecs.getincrementaldecoder("utf-8")("replace")
    buf = ""
    fd = proc.stdout.fileno()
    while True:
        chunk = os.read(fd, 1024)
        if not chunk:
            break
        buf += ANSI.sub("", dec.decode(chunk))
        parts = re.split(r"[\r\n]", buf)
        buf = parts.pop()
        for p in parts:
            if p.strip():
                on_line(p)
        if buf:
            on_partial(buf)
    if buf.strip():
        on_line(buf)
    return proc.wait()


# ---------------------------------------------------------------- Pico (.uf2)
def uf2_drives():
    """ไดรฟ์ที่มีไฟล์ INFO_UF2.TXT คือบอร์ด Pico ที่อยู่ในโหมด BOOTSEL คืน [(ไดรฟ์, เนื้อหา INFO_UF2.TXT)]"""
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.kernel32.SetErrorMode(1)       # ไม่ให้ Windows เด้งหน้าต่าง "ไม่มีดิสก์ในไดรฟ์"
            mask = ctypes.windll.kernel32.GetLogicalDrives()
            cands = ["%s:\\" % c for i, c in enumerate(string.ascii_uppercase) if mask >> i & 1 and i >= 2]
        except Exception:  # noqa: BLE001
            cands = ["%s:\\" % c for c in string.ascii_uppercase[2:]]
    else:
        cands = glob.glob("/media/*/*") + glob.glob("/run/media/*/*") + glob.glob("/Volumes/*")
    out = []
    for d in cands:
        info = os.path.join(d, "INFO_UF2.TXT")
        try:
            if os.path.isfile(info):
                with open(info, encoding="utf-8", errors="replace") as f:
                    out.append((d, f.read()))
        except OSError:
            pass
    return out


def pico_prefix_for(info, prefix):
    """เลือกไฟล์ให้ตรงชิปที่ต่ออยู่ (RP2040 = Pico, RP2350 = Pico 2) โดยคงรุ่นที่มี Wi-Fi ไว้ตามที่เลือก"""
    wifi = prefix.endswith("_W")
    if "RP2350" in info:
        return "RPI_PICO2_W" if wifi else "RPI_PICO2"
    if "RPI-RP2" in info or "RP2040" in info:
        return "RPI_PICO_W" if wifi else "RPI_PICO"
    return prefix


# ================================================================ หน้าต่างลงเฟิร์มแวร์
class FlashDialog(tk.Toplevel):
    def __init__(self, app, on_success=None):
        super().__init__(app.root)
        self.app = app
        self.on_success = on_success
        self.q = queue.Queue()
        self.proc = None
        self.busy = False
        self.cancel = threading.Event()
        self.local_file = None
        self.f, self.fb, self.fbig = app.f, app.fb, app.fbig
        self.title("ลง MicroPython ให้บอร์ด")
        self.geometry("840x720")
        self.minsize(700, 560)
        self.configure(bg="#F4F7FB")
        self.transient(app.root)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._build()
        self._poll()

    # ---------------------------------------------------------------- หน้าจอ
    def _build(self):
        bg = "#F4F7FB"
        self.board = self.app.board()
        self.profile = PROFILES.get(self.board["id"])
        top = tk.Frame(self, bg=bg, padx=16, pady=12)
        top.pack(fill="both", expand=True)
        tk.Label(top, text="⬇ ลง MicroPython ให้บอร์ด", font=(self.app.ff, 18, "bold"), bg=bg, fg="#1D2433",
                 anchor="w").pack(fill="x")
        port = self.app.cmb_port.get()
        desc = dict(self._ports()).get(port, "")
        tk.Label(top, text="บอร์ด: %s     พอร์ต: %s %s" % (self.board["name"], port or "(ยังไม่ได้เลือก)",
                                                           ("(" + desc + ")") if desc else ""),
                 font=self.f, bg=bg, fg="#5A6478", anchor="w", wraplength=780, justify="left").pack(fill="x", pady=(2, 8))

        reason = self._unsupported()
        if reason:
            tk.Label(top, text=reason, font=self.f, bg="#FFF4CF", fg="#633806", justify="left", anchor="w",
                     wraplength=770, padx=12, pady=10).pack(fill="x", pady=6)
            ttk.Button(top, text="ปิด", command=self.destroy).pack(anchor="e", pady=10)
            return

        if "bluetooth" in desc.lower():
            tk.Label(top, text="⚠ พอร์ตนี้เป็น Bluetooth ไม่ใช่บอร์ด เลือกพอร์ตที่ชื่อ CP210x / CH340 / USB Serial ที่หน้าหลัก",
                     font=self.fb, bg="#FDE2E0", fg="#8A1F14", anchor="w", wraplength=770, padx=12, pady=8,
                     justify="left").pack(fill="x", pady=4)

        opt = tk.Frame(top, bg=bg)
        opt.pack(fill="x", pady=4)
        tk.Label(opt, text="เฟิร์มแวร์:", font=self.f, bg=bg).pack(side="left")
        self.cmb_var = ttk.Combobox(opt, state="readonly", width=48, values=[v[0] for v in self.profile["variants"]])
        self.cmb_var.current(0)
        self.cmb_var.pack(side="left", padx=6)
        ttk.Button(opt, text="ใช้ไฟล์ในเครื่อง…", command=self._pick_file).pack(side="left", padx=6)
        self.lbl_src = tk.Label(top, text="จะดาวน์โหลดรุ่นล่าสุดจาก micropython.org ให้อัตโนมัติ (ครั้งต่อไปใช้ไฟล์เดิม ไม่ต้องโหลดซ้ำ)",
                                font=self.f, bg=bg, fg="#5A6478", anchor="w", wraplength=780, justify="left")
        self.lbl_src.pack(fill="x")
        if self.profile.get("note"):
            tk.Label(top, text="ℹ " + self.profile["note"], font=self.f, bg="#EEF1F6", fg="#1D2433", justify="left",
                     anchor="w", wraplength=770, padx=12, pady=8).pack(fill="x", pady=6)

        names = (["เตรียมไฟล์", "เข้าโหมด BOOTSEL", "คัดลอกเฟิร์มแวร์", "เสร็จ"] if self.profile["kind"] == "uf2"
                 else ["เตรียมไฟล์", "ต่อบอร์ด (กด BOOT)", "ล้างข้อมูลเก่า", "เขียนเฟิร์มแวร์", "เสร็จ"])
        steps = tk.Frame(top, bg=bg)
        steps.pack(fill="x", pady=8)
        self.step_lbls = []
        for i, n in enumerate(names):
            l = tk.Label(steps, text="%d %s" % (i + 1, n), font=self.f, bg="#E3E8F0", fg="#5A6478", padx=10, pady=5)
            l.pack(side="left", padx=(0, 6))
            self.step_lbls.append(l)

        self.banner = tk.Label(top, font=self.fbig, justify="left", anchor="w", wraplength=770, padx=16, pady=14)
        self.banner.pack(fill="x", pady=6)
        self._banner(self._intro(), "info")
        self.bar = ttk.Progressbar(top, mode="determinate", maximum=100)
        self.bar.pack(fill="x", pady=4)

        btns = tk.Frame(top, bg=bg)
        btns.pack(side="bottom", fill="x", pady=8)
        self.btn_start = ttk.Button(btns, text="▶ เริ่มลง MicroPython", style="Accent.TButton", command=self.start)
        self.btn_start.pack(side="left")
        self.btn_close = ttk.Button(btns, text="ปิด", command=self._close)
        self.btn_close.pack(side="right")
        self.btn_log = ttk.Button(btns, text="ดูรายละเอียด ▾", command=self._toggle_log)
        self.btn_log.pack(side="right", padx=6)
        self.log_frame = tk.Frame(top, bg=bg)
        self.txt_log = tk.Text(self.log_frame, height=6, font=("Consolas", 9), bg="#1D2433", fg="#D6DEEB", wrap="word")
        self.txt_log.pack(fill="both", expand=True)

    def _ports(self):
        try:
            from device import list_ports
            return list_ports()
        except Exception:  # noqa: BLE001
            return []

    def _unsupported(self):
        b = self.board
        if not b.get("micropython"):
            return ("%s รัน MicroPython ไม่ได้ ให้เขียนโค้ด C++ แล้วอัปโหลดด้วย Arduino IDE\n"
                    "ถ้ามีบอร์ด ESP32 หรือ Pico ให้เลือกรุ่นบอร์ดที่ช่องด้านบนก่อน แล้วกดปุ่มนี้อีกครั้ง" % b["name"])
        if b["id"] in NOT_SUPPORTED:
            return NOT_SUPPORTED[b["id"]]
        if not self.profile:
            return "บอร์ดรุ่นนี้ยังลงเฟิร์มแวร์จากโปรแกรมนี้ไม่ได้ ให้ใช้ Thonny: Tools → Options → Interpreter → Install or update MicroPython"
        if self.profile["kind"] == "esp" and not self.app.cmb_port.get():
            return "ยังไม่ได้เลือกพอร์ต USB\nเสียบบอร์ด กด 'ค้นหาพอร์ต' ที่หน้าหลัก แล้วกดปุ่มนี้อีกครั้ง"
        return None

    def _intro(self):
        if self.profile["kind"] == "uf2":
            return ("กด \"เริ่ม\" แล้วทำตามที่ขึ้นบนจอ\nจะต้องถอดสาย USB แล้วกดปุ่ม BOOTSEL ค้างไว้ตอนเสียบสายกลับ\n"
                    "ข้อมูลและโค้ดเดิมในบอร์ดยังอยู่ แต่ถ้าเป็นเฟิร์มแวร์อื่นจะถูกแทนที่")
        return ("เตรียมมือไว้ที่ปุ่ม BOOT บนบอร์ด แล้วกด \"เริ่ม\"\n"
                "เมื่อกรอบนี้เปลี่ยนเป็นสีส้ม ให้กด BOOT ค้างไว้ จนกว่าจะเป็นสีเขียวจึงปล่อย\n"
                "⚠ โค้ดและไฟล์เดิมในบอร์ดจะถูกลบทั้งหมด ใช้เวลาประมาณ 1–2 นาที ห้ามถอดสายระหว่างลง")

    def _banner(self, text, kind):
        colors = {"info": ("#EEF1F6", "#1D2433"), "boot": ("#FFB547", "#3D2200"), "go": ("#D8F3E4", "#0F5C3A"),
                  "work": ("#DCE7FB", "#1B45A0"), "ok": ("#1E8C5A", "#FFFFFF"), "err": ("#FDE2E0", "#8A1F14")}
        bg, fg = colors[kind]
        self.banner.configure(text=text, bg=bg, fg=fg, font=self.fb if kind == "err" else self.fbig)

    def _alert(self, times=8):
        """เสียงบี๊บ + กรอบข้อความกะพริบ (สำหรับผู้ที่ไม่ได้ยินเสียง ให้เห็นจังหวะที่ต้องกดปุ่ม)"""
        self.bell()
        base = self.banner.cget("bg")

        def blink(n):
            if n <= 0 or not self.winfo_exists():
                return
            cur = self.banner.cget("bg")
            if cur not in (base, "#C0392B"):     # ข้อความเปลี่ยนไปแล้ว (เช่น เป็นสีเขียว) หยุดกะพริบ
                return
            self.banner.configure(bg="#C0392B" if cur == base else base)
            self.after(250, blink, n - 1)
        blink(times)

    def _stage(self, n):
        for i, l in enumerate(self.step_lbls):
            if i < n:
                l.configure(bg="#D8F3E4", fg="#0F5C3A", text="✔" + l.cget("text").lstrip("✔▶"))
            elif i == n:
                l.configure(bg="#2457C5", fg="#FFFFFF", text="▶" + l.cget("text").lstrip("✔▶"))
            else:
                l.configure(bg="#E3E8F0", fg="#5A6478", text=l.cget("text").lstrip("✔▶"))

    def _toggle_log(self):
        if self.log_frame.winfo_ismapped():
            self.log_frame.pack_forget()
            self.btn_log.configure(text="ดูรายละเอียด ▾")
        else:
            self.log_frame.pack(fill="both", expand=True, pady=(6, 0))
            self.btn_log.configure(text="ซ่อนรายละเอียด ▴")

    def _log(self, text):
        self.txt_log.insert("end", text + "\n")
        self.txt_log.see("end")

    def _pick_file(self):
        ext = _ext(self.profile)
        path = filedialog.askopenfilename(parent=self, title="เลือกไฟล์เฟิร์มแวร์",
                                          filetypes=[("MicroPython firmware", "*." + ext), ("ทุกไฟล์", "*.*")])
        if path:
            self.local_file = path
            self.lbl_src.configure(text="ใช้ไฟล์: " + path, fg="#1B45A0")

    def _close(self):
        if self.busy and not messagebox.askyesno("ลง MicroPython", "กำลังลงเฟิร์มแวร์อยู่ ถ้าหยุดตอนนี้ต้องเริ่มใหม่\nต้องการหยุดหรือไม่",
                                                 parent=self):
            return
        self.cancel.set()
        if self.proc and self.proc.poll() is None:
            self.proc.kill()
        self.destroy()

    # ---------------------------------------------------------------- เริ่ม
    def start(self):
        if self.busy:
            return
        if self.profile["kind"] == "esp":
            if esptool_version() is None:
                if messagebox.askyesno("ลง MicroPython", "ต้องติดตั้งโปรแกรม esptool ก่อน (ใช้อินเทอร์เน็ต ไม่ถึง 1 นาที)\nติดตั้งเลยหรือไม่",
                                       parent=self):
                    self._run_bg(self._install_esptool)
                return
            if not messagebox.askyesno("ลง MicroPython", "โค้ดและไฟล์เดิมในบอร์ดจะถูกลบทั้งหมด\nต้องการลง MicroPython หรือไม่",
                                       parent=self):
                return
        self.app.link.stop()           # ปล่อยพอร์ตที่โปรแกรมนี้อาจเปิดค้างไว้ (เช่นหน้าดูข้อมูลเรียลไทม์)
        self.txt_log.delete("1.0", "end")
        self.cancel.clear()
        self._connected = self._verified = False
        self._chip_msg = ""
        self._out = []
        self._run_bg(self._job_esp if self.profile["kind"] == "esp" else self._job_uf2)

    def _run_bg(self, fn):
        self.busy = True
        self.btn_start.configure(state="disabled")
        self.cmb_var.configure(state="disabled")
        threading.Thread(target=fn, daemon=True).start()

    def _variant(self):
        return self.profile["variants"][self.cmb_var.current()]

    def _prepare(self, prefix, page):
        self.q.put(("stage", 0))
        if self.local_file:
            self.q.put(("log", "ใช้ไฟล์ในเครื่อง: " + self.local_file))
            return self.local_file
        self.q.put(("banner", "กำลังเตรียมไฟล์เฟิร์มแวร์ %s ..." % prefix, "work"))
        return get_firmware(prefix, page, _ext(self.profile), lambda t: self.q.put(("log", t)),
                            lambda p: self.q.put(("progress", p)))

    def _install_esptool(self):
        self.q.put(("banner", "กำลังติดตั้ง esptool ...", "work"))
        self.q.put(("indeterminate", True))
        try:
            self.proc = _popen([sys.executable, "-m", "pip", "install", "esptool"])
            code = stream(self.proc, lambda l: self.q.put(("log", l)), lambda p: None)
        except Exception as e:  # noqa: BLE001
            self.q.put(("log", str(e)))
            code = -1
        self.q.put(("indeterminate", False))
        if code == 0:
            self.q.put(("finish", None, "ติดตั้ง esptool แล้ว กด \"เริ่มลง MicroPython\" อีกครั้ง", "info"))
        else:
            self.q.put(("finish", None, "ติดตั้ง esptool ไม่สำเร็จ ตรวจอินเทอร์เน็ต หรือเปิด Command Prompt แล้วพิมพ์\n"
                                        "pip install esptool", "err"))

    # ---------------------------------------------------------------- ESP32 / ESP8266
    def _job_esp(self, baud=460800, path=None):
        label, prefix, page = self._variant()
        try:
            path = path or self._prepare(prefix, page)
        except Exception as e:  # noqa: BLE001
            self.q.put(("finish", False, str(e), "err"))
            return
        if self.cancel.is_set():
            return
        cmd = esptool_cmd(self.profile["chip"], self.app.cmb_port.get(), baud, self.profile["offset"], path,
                          esptool_version())
        self.q.put(("log", "> esptool " + " ".join(cmd[5:])))
        self.q.put(("stage", 1))
        self.q.put(("banner", "กำลังเชื่อมต่อบอร์ด ...", "work"))
        self.q.put(("progress", 0))
        try:
            self.proc = _popen(cmd)
            code = stream(self.proc, lambda l: self.q.put(("esp", l, True)), lambda p: self.q.put(("esp", p, False)))
        except Exception as e:  # noqa: BLE001
            self.q.put(("esp", str(e), True))
            code = -1
        self.q.put(("esp_exit", code, baud, path))

    def _esp_text(self, t, full):
        if full:
            self._log(t)
            self._out.append(t)
        if not self._connected and "Connecting" in t and self.banner.cget("bg") != "#FFB547":
            self._banner("👉 กดปุ่ม BOOT บนบอร์ดค้างไว้ตอนนี้\nกดค้างจนกว่ากรอบนี้จะเปลี่ยนเป็นสีเขียว แล้วจึงปล่อย\n"
                         "(ถ้าเกิน 10 วินาทียังไม่เขียว: กด BOOT ค้าง แล้วกด EN 1 ครั้ง)", "boot")
            self._alert()
        if not self._connected and re.search(r"Chip is|Connected to|Chip type", t):
            self._connected = True
            self._stage(2)
            self._banner("✔ ต่อบอร์ดได้แล้ว ปล่อยปุ่ม BOOT ได้\nกำลังล้างข้อมูลเก่าในบอร์ด (10–30 วินาที) ห้ามถอดสาย", "go")
        if "Erasing" in t:
            self._stage(2)
            self.bar.configure(mode="indeterminate")
            self.bar.start(15)
        m = re.search(r"(\d{1,3}(?:\.\d+)?)\s?%", t)
        if m and "Writing" in t:
            if str(self.bar.cget("mode")) != "determinate":
                self.bar.stop()
                self.bar.configure(mode="determinate")
                self._stage(3)
            pct = float(m.group(1))
            self.bar["value"] = pct
            self._banner("กำลังเขียน MicroPython ลงบอร์ด %d%%  ห้ามถอดสาย" % pct, "work")
        if "Hash of data verified" in t:
            self._verified = True

    def _esp_exit(self, code, baud, path):
        self.bar.stop()
        self.bar.configure(mode="determinate")
        if self.cancel.is_set():
            return
        text = "\n".join(self._out)
        if code == 0 and (self._verified or "Hard resetting" in text or "Leaving" in text):
            self.bar["value"] = 100
            self._finish(True, "✔ ลง MicroPython เรียบร้อยแล้ว\nบอร์ดกำลังรีสตาร์ต โปรแกรมจะตรวจบอร์ดให้อัตโนมัติ"
                               + ("\n(ถ้าตรวจไม่เจอ ให้กดปุ่ม RST บนบอร์ด 1 ครั้ง)" if self.profile["chip"] != "esp32" else ""),
                         "ok")
            return
        kind, msg, m = diagnose(text)
        if kind == "slow" and self._connected and baud > 115200:
            self._log("--- ลองใหม่ด้วยความเร็วต่ำลง (115200) ---")
            self._connected = False
            self._out = []
            self._banner("การส่งข้อมูลสะดุด กำลังลองใหม่ด้วยความเร็วต่ำลง ...", "work")
            threading.Thread(target=self._job_esp, args=(115200, path), daemon=True).start()
            return
        if kind == "wrongchip":
            real = m.group(1).upper()
            bid = CHIP_TO_BOARD.get(real)
            self._finish(False, "บอร์ดที่ต่ออยู่ใช้ชิป %s แต่ในโปรแกรมเลือกเป็น %s" % (real, self.board["name"]), "err")
            if bid and messagebox.askyesno("เลือกรุ่นบอร์ดผิด", "เปลี่ยนรุ่นบอร์ดเป็นชิป %s แล้วลองใหม่หรือไม่" % real, parent=self):
                ids = [b["id"] for b in self.app.kb.boards]
                self.app.cmb_board.current(ids.index(bid))
                self.app._board_changed()
                for w in self.winfo_children():
                    w.destroy()
                self._build()
            return
        self._finish(False, msg, "err")

    # ---------------------------------------------------------------- Pico
    def _job_uf2(self):
        label, prefix, page = self._variant()
        try:
            path = self._prepare(prefix, page)
        except Exception as e:  # noqa: BLE001
            self.q.put(("finish", False, str(e), "err"))
            return
        self.q.put(("stage", 1))
        self.q.put(("banner", "1. ถอดสาย USB ของ Pico ออก\n2. กดปุ่ม BOOTSEL บนบอร์ดค้างไว้\n"
                              "3. เสียบสาย USB กลับ แล้วจึงปล่อยปุ่ม\nโปรแกรมกำลังรอ ... (จะเห็นไดรฟ์ชื่อ RPI-RP2 หรือ RP2350)", "boot"))
        self.q.put(("bell",))
        drive = None
        for _ in range(180):
            if self.cancel.is_set():
                return
            found = uf2_drives()
            if found:
                drive, info = found[0]
                break
            time.sleep(1)
        if not drive:
            self.q.put(("finish", False, "ไม่พบไดรฟ์ของ Pico ภายใน 3 นาที\nลองเปลี่ยนสาย USB แล้วกดเริ่มใหม่", "err"))
            return
        self.q.put(("log", "พบไดรฟ์ %s\n%s" % (drive, info.strip())))
        want = pico_prefix_for(info, prefix)
        if want != prefix and not self.local_file:
            self.q.put(("log", "บอร์ดจริงเป็น %s เปลี่ยนไฟล์ให้ตรงชิป" % want))
            try:
                path = get_firmware(want, want, "uf2", lambda t: self.q.put(("log", t)), lambda p: None)
            except Exception as e:  # noqa: BLE001
                self.q.put(("finish", False, str(e), "err"))
                return
        self.q.put(("stage", 2))
        self.q.put(("banner", "✔ พบบอร์ดแล้ว ปล่อยปุ่มได้\nกำลังคัดลอกเฟิร์มแวร์ ห้ามถอดสาย ...", "go"))
        self.q.put(("indeterminate", True))
        try:
            shutil.copyfile(path, os.path.join(drive, os.path.basename(path)))
        except OSError as e:
            if os.path.exists(drive):          # ไดรฟ์หายไปแปลว่าบอร์ดรีสตาร์ตเองหลังคัดลอกเสร็จ ถือว่าสำเร็จ
                self.q.put(("indeterminate", False))
                self.q.put(("finish", False, "คัดลอกไฟล์ไม่สำเร็จ: %s" % e, "err"))
                return
        time.sleep(3)
        self.q.put(("indeterminate", False))
        self.q.put(("progress", 100))
        self.q.put(("finish", True, "✔ ลง MicroPython เรียบร้อยแล้ว\nบอร์ดรีสตาร์ตเองแล้ว โปรแกรมจะค้นหาพอร์ตและตรวจบอร์ดให้", "ok"))

    # ---------------------------------------------------------------- จบงาน
    def _finish(self, ok, msg, kind):
        self.busy = False
        self.proc = None
        self.btn_start.configure(state="normal", text="↻ ลองอีกครั้ง" if ok is False else "▶ เริ่มลง MicroPython")
        self.cmb_var.configure(state="readonly")
        self._banner(msg, kind)
        if ok:
            self._stage(len(self.step_lbls) - 1)
            self.step_lbls[-1].configure(bg="#1E8C5A", fg="#FFFFFF", text="✔" + self.step_lbls[-1].cget("text").lstrip("✔▶"))
            self.btn_start.configure(state="disabled")
            self.btn_close.configure(text="เสร็จ ปิดหน้าต่างนี้", style="Accent.TButton")
            if self.on_success:
                self.after(3000, self.on_success)
        elif ok is False and not self.log_frame.winfo_ismapped():
            self._toggle_log()

    def _poll(self):
        if not self.winfo_exists():
            return
        try:
            while True:
                ev = self.q.get_nowait()
                k = ev[0]
                if k == "log":
                    self._log(ev[1])
                elif k == "banner":
                    self._banner(ev[1], ev[2])
                elif k == "stage":
                    self._stage(ev[1])
                elif k == "progress":
                    self.bar["value"] = ev[1]
                elif k == "indeterminate":
                    if ev[1]:
                        self.bar.configure(mode="indeterminate")
                        self.bar.start(15)
                    else:
                        self.bar.stop()
                        self.bar.configure(mode="determinate")
                elif k == "bell":
                    self._alert()
                elif k == "esp":
                    self._esp_text(ev[1], ev[2])
                elif k == "esp_exit":
                    self._esp_exit(*ev[1:])
                elif k == "finish":
                    self._finish(*ev[1:])
        except queue.Empty:
            pass
        self.after(80, self._poll)

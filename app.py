# -*- coding: utf-8 -*-
"""โปรแกรมผู้ช่วย AI สำหรับเรียนไมโครคอนโทรลเลอร์ (Arduino / ESP32 / Pico)
รันด้วยคำสั่ง:  py -3 app.py  (หรือดับเบิลคลิก run.bat)
"""
import sys
if sys.version_info < (3, 8):
    sys.stderr.write("\nThis program needs Python 3.8 or newer. You are running Python %d.%d\n"
                     "Install Python 3 from https://www.python.org/downloads/ then run:  py -3 app.py\n\n"
                     % sys.version_info[:2])
    sys.exit(1)

import json
import os
import queue
import re
import shutil
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import tkinter.font as tkfont

from kb import KnowledgeBase, BASE
from generator import CodeGenerator, check_code
from ai_client import AIClient, extract_code
from device import BoardLink, Simulator, list_ports, parse_line, evaluate_rule, has_mpremote
from wiring import WiringCanvas, SIGNAL_COLORS
from wizard import WizardTab

VERSION = "2.0"
CONFIG_PATH = os.path.join(BASE, "config.json")
MY_CODE = os.path.join(BASE, "my_code")
IMAGES = os.path.join(BASE, "images")
DEFAULT_CONFIG = {
    "app_name": "Arduino AI Assistant", "school": "โรงเรียนของเรา", "board": "esp32-devkit",
    "ai_backend": "none", "claude_api_key": "", "claude_model": "claude-sonnet-5",
    "ollama_url": "http://localhost:11434", "ollama_model": "qwen2.5-coder:7b", "font_size": 12,
}
EXAMPLES = [
    "ให้ LED ขา 4 กระพริบทุก 1 วินาที",
    "ให้ไฟบนบอร์ดกระพริบทุก 0.5 วินาที",
    "หมุน Servo ขา 18 ไป 45 องศา",
    "ให้ Servo หมุนกวาดไปมา",
    "อ่านระยะทางด้วยอัลตราโซนิก ถ้าใกล้กว่า 20 ซม. ให้ Buzzer ดัง",
    "อ่านอุณหภูมิและความชื้นด้วย DHT11 แล้วแสดงบนจอ OLED",
    "ถ้าดินแห้งน้อยกว่า 30 ให้รีเลย์เปิดปั๊มน้ำ",
    "ถ้ามีคนเคลื่อนไหวให้ไฟ LED ติด",
    "ถ้าแสงน้อยกว่า 30 ให้ LED ติด",
    "ถ้าแก๊สมากกว่า 60 ให้บัซเซอร์ดัง และไฟ LED ติด",
    "อ่านค่าจอยสติ๊ก",
]
PALETTE = dict(bg="#F4F7FB", card="#FFFFFF", ink="#1D2433", muted="#5A6478", blue="#2457C5",
               green="#1E8C5A", orange="#D9661A", red="#C0392B")


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    return cfg


def pick_font(root):
    fams = set(tkfont.families(root))
    for f in ("Leelawadee UI", "Tahoma", "Noto Sans Thai", "Sarabun", "TH Sarabun New", "Loma", "Garuda"):
        if f in fams:
            return f
    return "TkDefaultFont"


class App:
    def __init__(self, root):
        self.root = root
        self.cfg = load_config()
        self.kb = KnowledgeBase()
        self.gen = CodeGenerator(self.kb)
        self.ai = AIClient(self.cfg)
        self.link = BoardLink()
        self.q = queue.Queue()
        self.result = None
        self.sim = None
        self.live_source = None      # "sim" | "board" | None
        self.history = {}
        self.last_error = ""
        self.chat_history = []
        self.ff = pick_font(root)
        fs = int(self.cfg.get("font_size", 12))
        self.f = (self.ff, fs)
        self.fb = (self.ff, fs, "bold")
        self.fbig = (self.ff, fs + 4, "bold")
        self.fmono = ("Consolas" if "Consolas" in tkfont.families(root) else "Courier", fs)
        root.geometry("1280x820")
        root.minsize(1050, 700)
        root.configure(bg=PALETTE["bg"])
        self._style()
        self._build()
        self._refresh_title()
        self.refresh_ports()
        self.nb.bind("<<NotebookTabChanged>>", lambda e: self._tab_changed())
        self.root.after(50, self._poll)
        self.root.after(300, self.generate)          # สร้างโค้ดตัวอย่างทันทีที่เปิดโปรแกรม

    # ================================================================ หน้าตา
    def _style(self):
        s = ttk.Style(self.root)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        s.configure(".", font=self.f, background=PALETTE["bg"])
        s.configure("TNotebook.Tab", font=self.fb, padding=(14, 6))
        s.configure("TButton", font=self.f, padding=(10, 5))
        s.configure("Accent.TButton", font=self.fb, foreground="#FFFFFF", background=PALETTE["blue"])
        s.map("Accent.TButton", background=[("active", "#1B45A0")])
        s.configure("TLabelframe.Label", font=self.fb)
        s.configure("Card.TFrame", background=PALETTE["card"])

    def _build(self):
        head = tk.Frame(self.root, bg=PALETTE["blue"])
        head.pack(fill="x")
        self.lbl_title = tk.Label(head, text="", fg="#FFFFFF", bg=PALETTE["blue"], font=(self.ff, 20, "bold"))
        self.lbl_title.pack(side="left", padx=16, pady=8)
        self.lbl_school = tk.Label(head, text="", fg="#DCE6FA", bg=PALETTE["blue"], font=self.f)
        self.lbl_school.pack(side="left", padx=4)
        self.lbl_ai = tk.Label(head, text="", fg="#FFFFFF", bg=PALETTE["blue"], font=self.fb)
        self.lbl_ai.pack(side="right", padx=16)

        bar = ttk.Frame(self.root, padding=(12, 8))
        bar.pack(fill="x")
        ttk.Label(bar, text="บอร์ด:").pack(side="left")
        self.board_names = [b["name"] + ("" if b["micropython"] else "  (C++ เท่านั้น)") for b in self.kb.boards]
        self.cmb_board = ttk.Combobox(bar, values=self.board_names, state="readonly", width=46)
        ids = [b["id"] for b in self.kb.boards]
        self.cmb_board.current(ids.index(self.cfg["board"]) if self.cfg["board"] in ids else 0)
        self.cmb_board.pack(side="left", padx=6)
        self.cmb_board.bind("<<ComboboxSelected>>", lambda e: self._board_changed())
        ttk.Label(bar, text="  พอร์ต USB:").pack(side="left")
        self.cmb_port = ttk.Combobox(bar, width=22)
        self.cmb_port.pack(side="left", padx=6)
        ttk.Button(bar, text="ค้นหาพอร์ต", command=self.refresh_ports).pack(side="left")
        self.var_use_ai = tk.BooleanVar(value=self.ai.available())
        ttk.Checkbutton(bar, text="ใช้ AI ช่วยสร้างโค้ด", variable=self.var_use_ai).pack(side="left", padx=16)
        self.lbl_status = ttk.Label(bar, text="", foreground=PALETTE["muted"])
        self.lbl_status.pack(side="right")

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tab_index = dict(wizard=0, code=1, wiring=2, live=3, chat=4, kb=5, settings=6)
        self.wizard = WizardTab(self.nb, self)
        self.nb.add(self.wizard, text="🧭 ผู้ช่วยนำทาง")
        self._tab_code()
        self._tab_wiring()
        self._tab_live()
        self._tab_chat()
        self._tab_kb()
        self._tab_settings()

    def board(self):
        return self.kb.boards[self.cmb_board.current()]

    def status(self, text):
        self.lbl_status.configure(text=text)

    def _refresh_title(self):
        self.lbl_title.configure(text=self.cfg["app_name"])
        self.lbl_school.configure(text=self.cfg["school"])
        self.root.title("%s  (เวอร์ชัน %s)" % (self.cfg["app_name"], VERSION))
        name = {"none": "AI: ปิด (ใช้แม่แบบ)", "claude": "AI: Claude", "ollama": "AI: Ollama (ในเครื่อง)"}[self.cfg["ai_backend"]]
        self.lbl_ai.configure(text=name)

    def _text(self, parent, **kw):
        frame = ttk.Frame(parent)
        t = tk.Text(frame, wrap=kw.pop("wrap", "word"), relief="flat", bd=0, padx=10, pady=8,
                    font=kw.pop("font", self.f), bg=kw.pop("bg", PALETTE["card"]), fg=PALETTE["ink"], undo=True, **kw)
        sb = ttk.Scrollbar(frame, command=t.yview)
        t.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        t.pack(side="left", fill="both", expand=True)
        return frame, t

    # ================================================================ แท็บ 1 สร้างโค้ด
    def _tab_code(self):
        tab = ttk.Frame(self.nb, padding=10)
        self.nb.add(tab, text="① สร้างโค้ด")
        top = ttk.LabelFrame(tab, text="พิมพ์คำสั่งภาษาไทย", padding=8)
        top.pack(fill="x")
        self.txt_cmd = tk.Text(top, height=2, font=self.fbig, relief="flat", padx=10, pady=6)
        self.txt_cmd.pack(fill="x")
        self.txt_cmd.insert("1.0", EXAMPLES[4])
        self.txt_cmd.bind("<Control-Return>", lambda e: (self.generate(), "break"))
        row = ttk.Frame(top)
        row.pack(fill="x", pady=(8, 0))
        ttk.Button(row, text="✨ สร้างโค้ด  (Ctrl+Enter)", style="Accent.TButton", command=self.generate).pack(side="left")
        ttk.Button(row, text="🔍 ตรวจโค้ด", command=self.check).pack(side="left", padx=6)
        ttk.Label(row, text="   ตัวอย่างคำสั่ง:").pack(side="left")
        self.cmb_ex = ttk.Combobox(row, values=EXAMPLES, state="readonly", width=58)
        self.cmb_ex.pack(side="left", padx=6)
        self.cmb_ex.bind("<<ComboboxSelected>>", lambda e: self._use_example())

        bot = ttk.Frame(tab)
        bot.pack(side="bottom", fill="x")
        files = ttk.Frame(tab)
        files.pack(side="bottom", fill="x", pady=(0, 6))
        mid = ttk.Panedwindow(tab, orient="horizontal")
        mid.pack(fill="both", expand=True, pady=10)
        left = ttk.LabelFrame(mid, text="โค้ด (แก้ไขได้)", padding=4)
        fr, self.txt_code = self._text(left, wrap="none", font=self.fmono, bg="#FBFCFE")
        fr.pack(fill="both", expand=True)
        right = ttk.LabelFrame(mid, text="การต่อสาย / คำเตือน / คำอธิบาย", padding=4)
        fr2, self.txt_info = self._text(right)
        fr2.pack(fill="both", expand=True)
        for tag, color in (("err", PALETTE["red"]), ("warn", PALETTE["orange"]), ("ok", PALETTE["green"]), ("h", PALETTE["blue"])):
            self.txt_info.tag_configure(tag, foreground=color, font=self.fb if tag == "h" else self.f)
        mid.add(left, weight=3)
        mid.add(right, weight=2)
        ttk.Button(files, text="📂 เปิดไฟล์โค้ด (.py / .ino)", command=self.open_code).pack(side="left")
        ttk.Button(files, text="⭐ เก็บเป็นโค้ดของฉัน", command=self.save_my_code).pack(side="left", padx=6)
        ttk.Label(files, text="โค้ดของฉัน:").pack(side="left", padx=(10, 4))
        self.cmb_my = ttk.Combobox(files, values=self._my_code_list(), state="readonly", width=26)
        self.cmb_my.pack(side="left")
        self.cmb_my.bind("<<ComboboxSelected>>", lambda e: self.open_code(os.path.join(MY_CODE, self.cmb_my.get())))
        ttk.Button(files, text="📋 คัดลอก", command=self.copy_code).pack(side="left", padx=(16, 6))
        ttk.Button(files, text="💾 บันทึกเป็นไฟล์", command=self.save_code).pack(side="left")
        ttk.Button(bot, text="▶ รันบนบอร์ด (ทดลอง)", command=self.run_board).pack(side="left")
        ttk.Button(bot, text="⬆ อัปโหลดเป็น main.py", command=self.upload_board).pack(side="left")
        ttk.Button(bot, text="■ หยุด", command=self.stop_all).pack(side="left", padx=6)
        self.btn_lib = ttk.Button(bot, text="📦 ติดตั้งไลบรารี", command=self.install_libs)
        self.btn_lib.pack(side="left", padx=6)
        ttk.Button(bot, text="ดูภาพการต่อวงจร ➜", style="Accent.TButton",
                   command=lambda: self.nb.select(self.tab_index["wiring"])).pack(side="right")

    def _tab_changed(self):
        if not hasattr(self, "wc"):
            return
        i = self.nb.index(self.nb.select())
        if not self.result or not self.result.components:
            return
        if i == self.tab_index["wiring"] and self.wc.step == 0 and not self.wc.live_on:
            self.wc.play()                          # เข้าแท็บวงจรแล้วเล่นแอนิเมชันเอง
        elif i == self.tab_index["live"] and self.live_source is None and not self.cmb_port.get():
            self.start_sim()                        # ไม่มีบอร์ดต่ออยู่ เริ่มโหมดจำลองให้เลย

    def _use_example(self):
        self.txt_cmd.delete("1.0", "end")
        self.txt_cmd.insert("1.0", self.cmb_ex.get())
        self.generate()

    def _board_changed(self):
        self.cfg["board"] = self.board()["id"]
        self._save_config(silent=True)
        self.wizard.board_changed()
        if self.txt_cmd.get("1.0", "end").strip():
            self.generate()

    def generate(self):
        cmd = self.txt_cmd.get("1.0", "end").strip()
        board = self.board()
        res = self.gen.generate(cmd, board["id"], self.cfg["app_name"])
        self.result = res
        if self.var_use_ai.get() and self.ai.available() and res.components and board["micropython"]:
            self._set_code("# " + self.cfg["app_name"] + " กำลังคิด...\n")
            self.status("AI กำลังเขียนโค้ด...")

            def work():
                try:
                    reply = self.ai.generate_code(cmd, board, res, self.kb)
                    self.q.put(("ai_code", reply))
                except Exception as e:  # noqa: BLE001
                    self.q.put(("ai_fail", str(e)))
            threading.Thread(target=work, daemon=True).start()
        else:
            self._show_result(res)
        self.wc.load(res, board)
        self._reset_live_ui()

    def _set_code(self, code):
        self.txt_code.delete("1.0", "end")
        self.txt_code.insert("1.0", code)

    def _show_result(self, res, ai_text=None):
        self._set_code(res.code)
        t = self.txt_info
        t.delete("1.0", "end")
        for e in res.errors:
            t.insert("end", "✖ " + e + "\n", "err")
        if res.wiring:
            t.insert("end", "การต่อสาย\n", "h")
            for w in res.wiring:
                t.insert("end", "• %s ขา %s  →  บอร์ด %s\n" % (w["comp_name"], w["comp_pin"], w["board_pin"]))
            t.insert("end", "\n")
        if res.warnings:
            t.insert("end", "ข้อควรระวัง\n", "h")
            for w in res.warnings:
                t.insert("end", "⚠ " + w + "\n", "warn")
            t.insert("end", "\n")
        if ai_text:
            t.insert("end", "คำอธิบายจาก AI\n", "h")
            t.insert("end", ai_text.strip() + "\n")
        elif res.explanation:
            t.insert("end", "คำอธิบาย\n", "h")
            for x in res.explanation:
                t.insert("end", "• " + x + "\n")
        if res.keys:
            t.insert("end", "\nค่าที่บอร์ดจะส่งกลับมา: " + ", ".join(res.keys) + "\n", "ok")
        libs = [c.get("library") for c in res.components if c.get("library")]
        self.btn_lib.configure(state="normal" if libs else "disabled")
        self.status("สร้างโค้ดเสร็จ" + (" (มีข้อผิดพลาด)" if res.errors else ""))

    # ---------- โค้ดจากไฟล์ และคลังโค้ดของฉัน
    def _my_code_list(self):
        os.makedirs(MY_CODE, exist_ok=True)
        return sorted(f for f in os.listdir(MY_CODE) if f.endswith((".py", ".ino")))

    def open_code(self, path=None):
        path = path or filedialog.askopenfilename(filetypes=[("โค้ด", "*.py *.ino *.txt"), ("ทุกไฟล์", "*.*")])
        if not path or not os.path.isfile(path):
            return
        with open(path, encoding="utf-8", errors="replace") as f:
            code = f.read()
        from generator import Result
        m = re.search(r"^(?:#|//) คำสั่ง:\s*(.+)$", code, re.M)
        if m:   # ไฟล์ที่โปรแกรมนี้เคยสร้าง: กู้แผนการต่อสายกลับมาให้ด้วย
            _, _, res = self.gen.plan(m.group(1), self.board()["id"])
            res.keys = [k for c in res.components if c["type"] == "sensor" for k in c.get("keys", [])]
            self.txt_cmd.delete("1.0", "end")
            self.txt_cmd.insert("1.0", m.group(1))
        else:
            res = Result()
            res.keys = list(dict.fromkeys(re.findall(r"print\(\s*[\"']([A-Za-z_]\w*)\s*[:=]", code)))
            res.explanation.append("โค้ดนี้ไม่ได้สร้างจากโปรแกรม จึงไม่มีภาพการต่อสาย ตรวจการต่อสายจากคอมเมนต์ในโค้ดเอง")
        res.code = code
        res.language = "cpp" if ("void setup" in code or path.lower().endswith(".ino")) else "micropython"
        if res.language == "cpp" and self.board()["micropython"]:
            res.warnings.append("ไฟล์นี้เป็นโค้ด C++ ของ Arduino บอร์ด MicroPython รันไม่ได้ ให้เปิดด้วย Arduino IDE")
        errs, warns = check_code(code, self.board()) if res.language == "micropython" else ([], [])
        res.errors += errs
        res.warnings += warns
        res.explanation.insert(0, "เปิดจากไฟล์: " + os.path.basename(path))
        if res.keys:
            res.explanation.append("ค่าที่พบในคำสั่ง print: " + ", ".join(res.keys) + " (แสดงเป็นกราฟในแท็บข้อมูลเรียลไทม์ได้)")
        self.result = res
        self._show_result(res)
        self.wc.load(res, self.board())
        self._reset_live_ui()
        self.nb.select(self.tab_index["code"])
        self.status("เปิดไฟล์แล้ว: " + os.path.basename(path))

    def save_my_code(self):
        name = simpledialog.askstring("เก็บเป็นโค้ดของฉัน", "ตั้งชื่อโค้ด:", parent=self.root)
        if not name:
            return
        name = re.sub(r'[\\/:*?"<>|]', "_", name.strip())
        ext = ".ino" if self.result is not None and self.result.language == "cpp" else ".py"
        os.makedirs(MY_CODE, exist_ok=True)
        path = os.path.join(MY_CODE, name + ext)
        if os.path.exists(path) and not messagebox.askyesno("เก็บโค้ด", "มีชื่อนี้แล้ว ต้องการเขียนทับหรือไม่"):
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.txt_code.get("1.0", "end"))
        self.cmb_my.configure(values=self._my_code_list())
        self.status("เก็บโค้ดแล้ว: my_code/" + name + ext)

    def load_thumb(self, item, size=200):
        """โหลดรูปจากคลังความรู้ ย่อให้พอดี รองรับ .jpg และรูปจากมือถือถ้ามี Pillow"""
        path = self.kb.image_path(item)
        if not path:
            return None
        try:
            from PIL import Image, ImageTk, ImageOps
            im = ImageOps.exif_transpose(Image.open(path))
            im.thumbnail((size, size))
            return ImageTk.PhotoImage(im)
        except ImportError:
            try:
                img = tk.PhotoImage(file=path)
                f = max(1, img.width() // size)
                return img.subsample(f, f)
            except tk.TclError:
                return None
        except Exception:  # noqa: BLE001
            return None

    def check(self):
        code = self.txt_code.get("1.0", "end")
        errs, warns = check_code(code, self.board())
        if not errs and not warns:
            messagebox.showinfo("ตรวจโค้ด", "ไม่พบปัญหา ✔")
        else:
            messagebox.showwarning("ตรวจโค้ด", "\n".join(["✖ " + e for e in errs] + ["⚠ " + w for w in warns]))

    def copy_code(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.txt_code.get("1.0", "end"))
        self.status("คัดลอกโค้ดแล้ว")

    def save_code(self):
        cpp = self.result is not None and self.result.language == "cpp"
        path = filedialog.asksaveasfilename(defaultextension=".ino" if cpp else ".py",
                                            initialfile="sketch.ino" if cpp else "main.py",
                                            filetypes=[("Arduino Sketch", "*.ino")] if cpp else [("MicroPython", "*.py")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.txt_code.get("1.0", "end"))
            self.status("บันทึกแล้ว: " + os.path.basename(path))

    # ================================================================ เชื่อมบอร์ดจริง
    def refresh_ports(self):
        ports = list_ports()
        self.cmb_port.configure(values=[p for p, _ in ports])
        if ports and not self.cmb_port.get():
            self.cmb_port.set(ports[0][0])
        self.status("พบ %d พอร์ต" % len(ports) if ports else "ไม่พบบอร์ด (ใช้โหมดจำลองได้)")

    def _can_run(self):
        b = self.board()
        if not b["micropython"] or (self.result and self.result.language == "cpp"):
            messagebox.showinfo("อัปโหลด", "บอร์ดนี้ใช้ภาษา C++ ให้กด 'บันทึกไฟล์' แล้วเปิดด้วย Arduino IDE")
            return False
        if not self.cmb_port.get():
            messagebox.showinfo("อัปโหลด", "ยังไม่ได้เลือกพอร์ต USB เสียบบอร์ดแล้วกด 'ค้นหาพอร์ต'")
            return False
        if not has_mpremote():
            messagebox.showinfo("อัปโหลด", "ต้องติดตั้ง mpremote ก่อน\nเปิด Command Prompt แล้วพิมพ์:\npip install mpremote pyserial")
            return False
        errs, _ = check_code(self.txt_code.get("1.0", "end"), b)
        if errs and not messagebox.askyesno("พบข้อผิดพลาด", "\n".join(errs) + "\n\nยังต้องการส่งโค้ดไปที่บอร์ดหรือไม่"):
            return False
        return True

    def run_board(self):
        if not self._can_run():
            return
        self._begin_board_live()
        self.link.run(self.cmb_port.get(), self.txt_code.get("1.0", "end"),
                      lambda l: self.q.put(("line", l)), lambda c: self.q.put(("done", c)))
        self.status("กำลังรันบนบอร์ด...")

    def upload_board(self):
        if not self._can_run():
            return
        port = self.cmb_port.get()

        def done(code):
            self.q.put(("done", code))
            if code == 0:
                self.q.put(("uploaded", port))
        self.link.upload(port, self.txt_code.get("1.0", "end"), lambda l: self.q.put(("line", l)), done)
        self.status("กำลังอัปโหลด...")
        self.nb.select(self.tab_index['live'])

    def install_libs(self):
        if not self.result or not self.cmb_port.get():
            return
        libs = [c["library"] for c in self.result.components if c.get("library")]
        for lib in libs:
            self.link.install_lib(self.cmb_port.get(), lib, lambda l: self.q.put(("line", l)), lambda c: self.q.put(("done", c)))
        self.nb.select(self.tab_index['live'])

    def stop_all(self):
        self.link.stop()
        self.stop_live()
        self.status("หยุดแล้ว")

    # ================================================================ แท็บ 2 ต่อวงจร
    def _tab_wiring(self):
        tab = ttk.Frame(self.nb, padding=10)
        self.nb.add(tab, text="② ภาพการต่อวงจร")
        self.lbl_cap = tk.Label(tab, text="", font=self.fbig, bg="#E4ECFB", fg=PALETTE["ink"], anchor="w",
                                justify="left", padx=14, pady=10, wraplength=1150)
        self.lbl_cap.pack(fill="x")
        ctl = ttk.Frame(tab)
        ctl.pack(fill="x", pady=8)
        ttk.Button(ctl, text="↺ เริ่มใหม่", command=lambda: self.wc.reset()).pack(side="left")
        ttk.Button(ctl, text="◀ ย้อน", command=lambda: self.wc.prev_step()).pack(side="left", padx=6)
        ttk.Button(ctl, text="ถัดไป ▶", command=lambda: self.wc.next_step()).pack(side="left")
        ttk.Button(ctl, text="⏯ เล่นทั้งหมด", style="Accent.TButton", command=lambda: self.wc.play()).pack(side="left", padx=6)
        ttk.Button(ctl, text="แสดงทุกเส้น", command=lambda: self.wc.show_all()).pack(side="left")
        ttk.Button(ctl, text="⚡ ดูการทำงาน (จำลอง)", command=self.start_sim).pack(side="left", padx=(24, 6))
        ttk.Button(ctl, text="■ หยุด", command=self.stop_live).pack(side="left")
        leg = ttk.Frame(ctl)
        leg.pack(side="right")
        for color, name in (("#E24B4A", "5V"), ("#EF9F27", "3.3V"), ("#5F5E5A", "GND"), ("#378ADD", "สัญญาณ")):
            tk.Label(leg, text="━━", fg=color, font=self.fb, bg=PALETTE["bg"]).pack(side="left")
            ttk.Label(leg, text=name + "  ").pack(side="left")
        frame = ttk.Frame(tab)
        frame.pack(fill="both", expand=True)
        self.wc = WiringCanvas(frame, font_family=self.ff, on_caption=self._caption, width=900, height=560)
        sb = ttk.Scrollbar(frame, command=self.wc.yview)
        self.wc.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.wc.pack(side="left", fill="both", expand=True)
        self.wc.load(None, self.board())

    def _caption(self, text, step, total):
        prefix = "👀 " + ("[%d/%d] " % (step, total) if total and step else "")
        self.lbl_cap.configure(text=prefix + text)

    # ================================================================ แท็บ 3 เรียลไทม์
    def _tab_live(self):
        tab = ttk.Frame(self.nb, padding=10)
        self.nb.add(tab, text="③ ข้อมูลเรียลไทม์")
        ctl = ttk.Frame(tab)
        ctl.pack(fill="x")
        ttk.Button(ctl, text="⚡ เริ่มโหมดจำลอง (ไม่ต้องมีบอร์ด)", style="Accent.TButton", command=self.start_sim).pack(side="left")
        ttk.Button(ctl, text="🔌 อ่านจากบอร์ดจริง", command=self.monitor_board).pack(side="left", padx=6)
        ttk.Button(ctl, text="■ หยุด", command=self.stop_all).pack(side="left")
        self.btn_explain = ttk.Button(ctl, text="🤖 ให้ AI อธิบาย Error", command=self.explain_error, state="disabled")
        self.btn_explain.pack(side="left", padx=16)
        self.lbl_src = ttk.Label(ctl, text="", foreground=PALETTE["muted"])
        self.lbl_src.pack(side="right")
        self.cards = ttk.Frame(tab)
        self.cards.pack(fill="x", pady=10)
        self.card_widgets = {}
        self.chart = tk.Canvas(tab, height=260, bg=PALETTE["card"], highlightthickness=0)
        self.chart.pack(fill="x")
        lf = ttk.LabelFrame(tab, text="ข้อความจากบอร์ด (Serial)", padding=4)
        lf.pack(fill="both", expand=True, pady=(10, 0))
        fr, self.txt_log = self._text(lf, font=self.fmono, height=8, bg="#1D2433")
        self.txt_log.configure(fg="#DDF2E7", insertbackground="#FFFFFF")
        self.txt_log.tag_configure("err", foreground="#F09595")
        fr.pack(fill="both", expand=True)

    def _reset_live_ui(self):
        self.stop_live()
        for w in self.cards.winfo_children():
            w.destroy()
        self.card_widgets, self.history = {}, {}
        keys = list(self.result.keys) if self.result else []
        acts = [c for c in (self.result.components if self.result else []) if c["type"] == "actuator"]
        for i, k in enumerate(keys):
            self._make_card(k, SIGNAL_COLORS[i % len(SIGNAL_COLORS)])
        for a in acts:
            self._make_card("@" + a["id"], "#BA7517", title=a["name_th"][:22])
        self.chart.delete("all")
        self.chart.create_text(20, 130, anchor="w", font=self.f, fill=PALETTE["muted"],
                               text="กราฟจะแสดงเมื่อเริ่มโหมดจำลอง หรืออ่านค่าจากบอร์ดจริง" if keys else "โค้ดนี้ไม่มีเซนเซอร์ส่งค่ากลับมา")

    def _make_card(self, key, color, title=None):
        f = tk.Frame(self.cards, bg=PALETTE["card"], highlightbackground=color, highlightthickness=2, padx=14, pady=8)
        f.pack(side="left", padx=(0, 10))
        tk.Label(f, text=title or key, bg=PALETTE["card"], fg=PALETTE["muted"], font=self.f).pack(anchor="w")
        v = tk.Label(f, text="–", bg=PALETTE["card"], fg=color, font=(self.ff, 26, "bold"))
        v.pack(anchor="w")
        self.card_widgets[key] = (f, v)

    def start_sim(self):
        if not self.result or not self.result.components:
            messagebox.showinfo("โหมดจำลอง", "สร้างโค้ดก่อน แล้วจึงเริ่มโหมดจำลอง")
            return
        self.link.stop()
        self._reset_live_ui()
        self.sim = Simulator(self.result, self.kb)
        self.live_source = "sim"
        self.lbl_src.configure(text="แหล่งข้อมูล: จำลอง")
        self.wc.start_live()
        self._sim_tick()

    def _sim_tick(self):
        if self.live_source != "sim" or not self.sim:
            return
        vals = self.sim.step()
        for k, v in vals.items():
            self._on_line("%s: %s" % (k, v))
        if not vals:
            acts = {c["id"]: True for c in self.result.components if c["type"] == "actuator"}
            self._apply_states(acts)
        self.root.after(700, self._sim_tick)

    def _begin_board_live(self):
        self._reset_live_ui()
        self.live_source = "board"
        self.lbl_src.configure(text="แหล่งข้อมูล: บอร์ดจริง")
        self.wc.start_live()
        self.nb.select(self.tab_index['live'])

    def monitor_board(self):
        if not self.cmb_port.get():
            messagebox.showinfo("บอร์ดจริง", "ยังไม่ได้เลือกพอร์ต USB")
            return
        self._begin_board_live()
        self.link.monitor(self.cmb_port.get(), lambda l: self.q.put(("line", l)))

    def stop_live(self):
        self.live_source = None
        self.sim = None
        self.wc.stop_live()
        self.lbl_src.configure(text="")

    def _on_line(self, line):
        is_err = any(w in line for w in ("Traceback", "Error", "error:", "ไม่พบ", "ไม่ได้"))
        self.txt_log.insert("end", line + "\n", "err" if is_err else "")
        self.txt_log.see("end")
        if int(self.txt_log.index("end-1c").split(".")[0]) > 600:
            self.txt_log.delete("1.0", "200.0")
        if is_err:
            self.last_error += line + "\n"
            self.btn_explain.configure(state="normal" if self.ai.available() else "disabled")
        vals = parse_line(line)
        if not vals:
            return
        for k, v in vals.items():
            self.history.setdefault(k, []).append(v)
            self.history[k] = self.history[k][-120:]
            if k not in self.card_widgets:
                self._make_card(k, SIGNAL_COLORS[len(self.card_widgets) % len(SIGNAL_COLORS)])
            self.card_widgets[k][1].configure(text=_fmt(v))
        states = evaluate_rule(self.result.rule if self.result else None, {k: h[-1] for k, h in self.history.items()}, [])
        self._apply_states(states, vals)
        self._draw_chart()

    def _apply_states(self, states, vals=None):
        for aid, on in states.items():
            w = self.card_widgets.get("@" + aid)
            if w:
                w[1].configure(text="ทำงาน" if on else "หยุด", fg="#BA7517" if on else "#888780")
        if self.wc.live_on:
            self.wc.set_live(vals or {}, states)

    def _draw_chart(self):
        c = self.chart
        c.delete("all")
        W = max(600, c.winfo_width())
        H = 260
        L, R, T, B = 60, 20, 20, 30
        c.create_rectangle(L, T, W - R, H - B, outline="#D9DFEA")
        keys = [k for k in self.history if self.history[k]]
        for i, k in enumerate(keys):
            data = self.history[k]
            lo, hi = min(data), max(data)
            if self.sim and k in self.sim.ranges:
                lo, hi = self.sim.ranges[k][0], self.sim.ranges[k][1]
            if hi - lo < 1e-6:
                hi = lo + 1
            color = SIGNAL_COLORS[i % len(SIGNAL_COLORS)]
            n = len(data)
            pts = []
            for j, v in enumerate(data):
                x = L + (W - L - R) * (j / 119 if n > 1 else 0)
                y = (H - B) - (H - B - T) * (v - lo) / (hi - lo)
                pts += [x, y]
            if len(pts) >= 4:
                c.create_line(*pts, fill=color, width=3, smooth=True)
            c.create_text(L + 10 + i * 170, H - 12, anchor="w", fill=color, font=self.fb,
                          text="━ %s (%s–%s)" % (k, _fmt(lo), _fmt(hi)))
        rule = self.result.rule if self.result else None
        if rule and rule["key"] in self.history and rule["op"] != "==":
            data = self.history[rule["key"]]
            lo, hi = (self.sim.ranges[rule["key"]][:2] if self.sim and rule["key"] in self.sim.ranges else (min(data), max(data)))
            if hi > lo:
                y = (H - B) - (H - B - T) * (rule["thr"] - lo) / (hi - lo)
                if T <= y <= H - B:
                    c.create_line(L, y, W - R, y, fill=PALETTE["orange"], dash=(6, 4), width=2)
                    c.create_text(W - R - 6, y - 10, anchor="e", fill=PALETTE["orange"], font=self.f,
                                  text="เส้นเงื่อนไข %s %s" % (rule["op"], rule["thr"]))

    def explain_error(self):
        if not self.last_error:
            return
        self.nb.select(self.tab_index['chat'])
        self._chat_add("คุณ", "ช่วยอธิบาย Error นี้:\n" + self.last_error[-600:])
        code, board, err = self.txt_code.get("1.0", "end"), self.board(), self.last_error
        self.last_error = ""
        threading.Thread(target=lambda: self._ai_job(lambda: self.ai.explain_error(err, code, board)), daemon=True).start()

    # ================================================================ แท็บ 4 ถาม AI
    def _tab_chat(self):
        tab = ttk.Frame(self.nb, padding=10)
        self.nb.add(tab, text="④ ถาม AI")
        fr, self.txt_chat = self._text(tab, state="normal")
        fr.pack(fill="both", expand=True)
        self.txt_chat.tag_configure("me", foreground=PALETTE["blue"], font=self.fb)
        self.txt_chat.tag_configure("ai", foreground=PALETTE["green"], font=self.fb)
        row = ttk.Frame(tab)
        row.pack(fill="x", pady=(8, 0))
        self.ent_chat = ttk.Entry(row, font=self.fbig)
        self.ent_chat.pack(side="left", fill="x", expand=True)
        self.ent_chat.bind("<Return>", lambda e: self.send_chat())
        ttk.Button(row, text="ส่งคำถาม", style="Accent.TButton", command=self.send_chat).pack(side="left", padx=6)
        self._chat_add(self.cfg["app_name"], "สวัสดีครับ ถามเรื่องบอร์ด เซนเซอร์ หรือการต่อวงจรได้เลย เช่น \"DHT11 ต่อกับ ESP32 ยังไง\"")

    def _chat_add(self, who, text):
        self.txt_chat.insert("end", who + ":\n", "me" if who == "คุณ" else "ai")
        self.txt_chat.insert("end", text.strip() + "\n\n")
        self.txt_chat.see("end")

    def send_chat(self):
        q = self.ent_chat.get().strip()
        if not q:
            return
        self.ent_chat.delete(0, "end")
        self._chat_add("คุณ", q)
        if not self.ai.available():
            self._chat_add(self.cfg["app_name"], self._offline_answer(q))
            return
        board = self.board()
        hist = list(self.chat_history[-6:])
        threading.Thread(target=lambda: self._ai_job(lambda: self.ai.ask(q, self.kb, board, hist), q), daemon=True).start()

    def _ai_job(self, fn, question=None):
        self.q.put(("status", "AI กำลังคิด..."))
        try:
            ans = fn()
            if question:
                self.chat_history += [{"role": "user", "content": question}, {"role": "assistant", "content": ans}]
            self.q.put(("chat", ans))
        except Exception as e:  # noqa: BLE001
            self.q.put(("chat", "เชื่อมต่อ AI ไม่ได้: %s\nตรวจการตั้งค่าในแท็บ ⚙ ตั้งค่า" % e))

    def _offline_answer(self, q):
        found = [c for c, _ in self.kb.detect(q)]
        if not found:
            return "(โหมดไม่ใช้ AI) ยังไม่พบอุปกรณ์ในคำถาม ลองพิมพ์ชื่ออุปกรณ์ เช่น DHT11, Servo หรือดูที่แท็บคลังความรู้"
        board = self.board()
        out = ["(โหมดไม่ใช้ AI ตอบจากคลังความรู้)"]
        for c in found:
            res = self.gen.generate("อ่าน " + c["keywords"][0] if c["type"] == "sensor" else c["keywords"][0], board["id"])
            out.append("\n%s — %s" % (c["name_th"], c["explain_th"]))
            out.append("แรงดัน: %s" % c["voltage"])
            for w in res.wiring:
                if w["comp"] == c["id"]:
                    out.append("• ขา %s → %s" % (w["comp_pin"], w["board_pin"]))
            for w in c.get("warnings", []):
                out.append("⚠ " + w)
        return "\n".join(out)

    # ================================================================ แท็บ 5 คลังความรู้
    def _tab_kb(self):
        tab = ttk.Frame(self.nb, padding=10)
        self.nb.add(tab, text="⑤ คลังความรู้")
        left = ttk.Frame(tab)
        left.pack(side="left", fill="y")
        self.ent_search = ttk.Entry(left, font=self.f, width=30)
        self.ent_search.pack(fill="x")
        self.ent_search.bind("<KeyRelease>", lambda e: self._kb_fill())
        btns = ttk.Frame(left)
        btns.pack(side="bottom", fill="x")      # ปุ่มอยู่ล่างสุดเสมอ ไม่ถูกรายการดันตกขอบจอ
        ttk.Button(btns, text="ใช้อุปกรณ์นี้ในคำสั่ง", command=self._kb_use).pack(fill="x")
        ttk.Button(btns, text="🖼 เพิ่ม / เปลี่ยนรูป", command=self._kb_add_image).pack(fill="x", pady=4)
        ttk.Button(btns, text="➕ เพิ่มอุปกรณ์ใหม่", command=lambda: NewComponentDialog(self)).pack(fill="x")
        self.lst_kb = tk.Listbox(left, font=self.f, width=38, height=10, activestyle="none", relief="flat")
        self.lst_kb.pack(fill="both", expand=True, pady=6)
        self.lst_kb.bind("<<ListboxSelect>>", lambda e: self._kb_show())
        right = ttk.Frame(tab)
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))
        self.lbl_img = tk.Label(right, bg=PALETTE["bg"], text="")
        self.lbl_img.pack(anchor="w")
        fr, self.txt_kb = self._text(right)
        fr.pack(fill="both", expand=True)
        self.txt_kb.tag_configure("h", font=self.fbig, foreground=PALETTE["blue"])
        self.txt_kb.tag_configure("warn", foreground=PALETTE["orange"])
        self._kb_items = []
        self._kb_fill()

    def _kb_fill(self):
        self._kb_items = self.kb.search(self.ent_search.get())
        self.lst_kb.delete(0, "end")
        for kind, it in self._kb_items:
            if kind == "board":
                self.lst_kb.insert("end", "🟦 " + it["name"])
            else:
                self.lst_kb.insert("end", "🔹 %s  (%s)" % (it["name_en"], it["category"]))

    def _kb_show(self):
        sel = self.lst_kb.curselection()
        if not sel:
            return
        kind, it = self._kb_items[sel[0]]
        t = self.txt_kb
        t.delete("1.0", "end")
        self._img = self.load_thumb(it, 320)
        self.lbl_img.configure(image=self._img or "",
                               text="" if self._img else "(ยังไม่มีรูป กดปุ่ม \"เพิ่ม / เปลี่ยนรูป\" ด้านซ้าย)")
        if kind == "board":
            t.insert("end", it["name"] + "\n", "h")
            t.insert("end", "เขียน MicroPython ได้: %s\n" % ("ได้ ✔" if it["micropython"] else "ไม่ได้ (ใช้ C++)"))
            t.insert("end", "แรงดันขาสัญญาณ: %sV\nวิธีลงโปรแกรม: %s\n\n%s\n\n" % (it["logic_v"], it["flash_tool"], it["notes_th"]))
            p = it["pools"]
            t.insert("end", "ขาแนะนำสำหรับส่งสัญญาณออก: %s\n" % ", ".join(map(str, p.get("out", [])[:12])))
            t.insert("end", "ขาอ่านค่าแอนะล็อก (ADC): %s\n" % ", ".join(map(str, p.get("adc", []))))
            if it.get("i2c"):
                t.insert("end", "I2C: SDA = %s, SCL = %s\n" % (it["i2c"]["sda"], it["i2c"]["scl"]))
            if it.get("input_only"):
                t.insert("end", "⚠ ขารับข้อมูลอย่างเดียว: %s\n" % ", ".join(map(str, it["input_only"])), "warn")
            if it.get("forbidden_list"):
                t.insert("end", "⚠ ห้ามใช้: %s\n" % ", ".join(map(str, it["forbidden_list"])), "warn")
            if it.get("onboard"):
                t.insert("end", "\nอุปกรณ์บนบอร์ด: %s\n" % ", ".join("%s=%s" % kv for kv in it["onboard"].items()))
        else:
            t.insert("end", "%s\n" % it["name_th"], "h")
            t.insert("end", "%s | หมวด: %s | แรงดัน: %s\n\n%s\n\n" % (it["name_en"], it["category"], it["voltage"], it["explain_th"]))
            t.insert("end", "ขาของอุปกรณ์:\n")
            for p in it["pins"]:
                t.insert("end", "• %s (%s)\n" % (p["label"], {"power5": "ไฟ 5V", "power3": "ไฟ 3.3V", "gnd": "GND"}.get(p["kind"], "สัญญาณ")))
            for w in it.get("warnings", []):
                t.insert("end", "⚠ " + w + "\n", "warn")
            if it.get("library"):
                t.insert("end", "\nติดตั้งไลบรารี: mpremote mip install %s\n" % it["library"])
            t.insert("end", "\nคำค้นที่ใช้ในคำสั่งได้: " + ", ".join(it["keywords"]) + "\n")

    def _kb_add_image(self):
        sel = self.lst_kb.curselection()
        if not sel:
            messagebox.showinfo("เพิ่มรูป", "เลือกบอร์ดหรืออุปกรณ์ในรายการด้านซ้ายก่อน")
            return
        kind, it = self._kb_items[sel[0]]
        src = filedialog.askopenfilename(filetypes=[("รูปภาพ", "*.png *.jpg *.jpeg *.gif *.webp"), ("ทุกไฟล์", "*.*")])
        if not src:
            return
        stem = os.path.splitext(os.path.basename(it.get("image") or (it["id"] + ".png")))[0]
        os.makedirs(IMAGES, exist_ok=True)
        dst = os.path.join(IMAGES, stem + ".png")
        try:
            from PIL import Image, ImageOps
            im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
            im.thumbnail((480, 480))
            im.save(dst)
        except ImportError:
            if not src.lower().endswith(".png"):
                messagebox.showwarning("เพิ่มรูป", "ต้องติดตั้ง Pillow ก่อนจึงจะใช้ไฟล์ .jpg ได้ (ดับเบิลคลิก install.bat อีกครั้ง)")
                return
            shutil.copy(src, dst)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("เพิ่มรูป", "เปิดรูปไม่ได้: %s" % e)
            return
        for ext in (".jpg", ".jpeg", ".webp", ".JPG", ".JPEG"):   # ลบรูปเก่าที่ชื่อเดียวกัน
            old = os.path.join(IMAGES, stem + ext)
            if os.path.exists(old):
                os.remove(old)
        self._kb_show()
        self.status("เพิ่มรูปแล้ว: images/" + os.path.basename(dst))

    def reload_kb(self):
        self.kb = KnowledgeBase()
        self.gen.kb = self.kb
        self._kb_fill()

    def _kb_use(self):
        sel = self.lst_kb.curselection()
        if not sel:
            return
        kind, it = self._kb_items[sel[0]]
        if kind == "board":
            self.cmb_board.current(self.kb.boards.index(it))
            self._board_changed()
        else:
            self.txt_cmd.delete("1.0", "end")
            self.txt_cmd.insert("1.0", ("อ่านค่า " if it["type"] == "sensor" else "ทดสอบ ") + it["keywords"][0])
            self.generate()
        self.nb.select(self.tab_index['code'])

    # ================================================================ แท็บ 6 ตั้งค่า
    def _tab_settings(self):
        tab = ttk.Frame(self.nb, padding=20)
        self.nb.add(tab, text="⚙ ตั้งค่า")
        self.set_vars = {}
        rows = [("app_name", "ชื่อ AI ของคุณ (แสดงบนหัวโปรแกรม)"), ("school", "ชื่อโรงเรียน"),
                ("claude_api_key", "Claude API Key"), ("claude_model", "ชื่อโมเดล Claude"),
                ("ollama_url", "ที่อยู่ Ollama"), ("ollama_model", "ชื่อโมเดล Ollama"), ("font_size", "ขนาดตัวอักษร (เปิดโปรแกรมใหม่)")]
        for i, (k, label) in enumerate(rows):
            ttk.Label(tab, text=label).grid(row=i, column=0, sticky="w", pady=5)
            v = tk.StringVar(value=str(self.cfg.get(k, "")))
            e = ttk.Entry(tab, textvariable=v, width=60, font=self.f, show="•" if k == "claude_api_key" else "")
            e.grid(row=i, column=1, sticky="w", padx=10)
            self.set_vars[k] = v
        ttk.Label(tab, text="สมอง AI").grid(row=len(rows), column=0, sticky="nw", pady=10)
        self.var_backend = tk.StringVar(value=self.cfg["ai_backend"])
        box = ttk.Frame(tab)
        box.grid(row=len(rows), column=1, sticky="w", padx=10, pady=10)
        for val, text in (("none", "ไม่ใช้ AI — ใช้แม่แบบที่ตรวจแล้ว ทำงานออฟไลน์"),
                          ("claude", "Claude API — แม่นยำที่สุด ต้องมีอินเทอร์เน็ต"),
                          ("ollama", "Ollama — รันโมเดลในเครื่องเอง ฟรี ไม่ต้องมีอินเทอร์เน็ต")):
            ttk.Radiobutton(box, text=text, value=val, variable=self.var_backend).pack(anchor="w")
        ttk.Button(tab, text="💾 บันทึกการตั้งค่า", style="Accent.TButton", command=self._save_config).grid(
            row=len(rows) + 1, column=1, sticky="w", padx=10, pady=10)
        ttk.Label(tab, foreground=PALETTE["muted"], wraplength=900, justify="left", text=(
            "หมายเหตุ: API Key ถูกเก็บในไฟล์ config.json บนเครื่องนี้ อย่าแชร์ไฟล์นี้ให้นักเรียน "
            "หรือกำหนดผ่านตัวแปรระบบ ANTHROPIC_API_KEY แทนได้")).grid(row=len(rows) + 2, column=0, columnspan=2, sticky="w")

    def _save_config(self, silent=False):
        if hasattr(self, "set_vars"):
            for k, v in self.set_vars.items():
                self.cfg[k] = v.get().strip()
            self.cfg["ai_backend"] = self.var_backend.get()
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.cfg, f, ensure_ascii=False, indent=2)
        self.ai.config = self.cfg
        self._refresh_title()
        self.var_use_ai.set(self.ai.available())
        if not silent:
            messagebox.showinfo("ตั้งค่า", "บันทึกแล้ว")

    # ================================================================ คิวงานจากเธรด
    def _poll(self):
        try:
            while True:
                kind, data = self.q.get_nowait()
                if kind == "line":
                    self._on_line(data)
                elif kind == "done":
                    self.status("เสร็จ" if data == 0 else "หยุดทำงาน (รหัส %s)" % data)
                elif kind == "uploaded":
                    self._on_line("✔ อัปโหลด main.py แล้ว กำลังอ่านค่าจากบอร์ด...")
                    self._begin_board_live()
                    self.link.monitor(data, lambda l: self.q.put(("line", l)))
                elif kind == "ai_code":
                    code = extract_code(data)
                    if code:
                        self.result.code = code
                        info = data.split("```")[-1]
                        errs, warns = check_code(code, self.board())
                        self.result.errors = errs + self.result.errors
                        self.result.warnings += warns
                        self._show_result(self.result, ai_text=info)
                    else:
                        self._show_result(self.result, ai_text="AI ไม่ได้ส่งโค้ดกลับมา จึงใช้โค้ดจากแม่แบบแทน\n\n" + data)
                    self.status("AI เขียนโค้ดเสร็จ")
                elif kind == "ai_fail":
                    self._show_result(self.result, ai_text="เชื่อมต่อ AI ไม่ได้ (%s) จึงใช้โค้ดจากแม่แบบแทน" % data)
                elif kind == "chat":
                    self._chat_add(self.cfg["app_name"], data)
                    self.status("")
                elif kind == "status":
                    self.status(data)
        except queue.Empty:
            pass
        self.root.after(50, self._poll)


def _fmt(v):
    return str(int(v)) if float(v).is_integer() else "%.1f" % v


class NewComponentDialog(tk.Toplevel):
    """ฟอร์มเพิ่มอุปกรณ์ใหม่ลงคลังความรู้ (บันทึกลง knowledge/components.json)"""
    FIELDS = [("id", "รหัสอุปกรณ์ (ภาษาอังกฤษ ไม่มีช่องว่าง)", "bh1750"),
              ("name_th", "ชื่อภาษาไทย", "เซนเซอร์วัดความเข้มแสง BH1750"),
              ("name_en", "ชื่อภาษาอังกฤษ", "BH1750"),
              ("category", "หมวด", "แสง"),
              ("keywords", "คำที่นักเรียนอาจพิมพ์ (คั่นด้วย ,) ใส่คำแรกเป็นคำเฉพาะของอุปกรณ์", "bh1750, ความเข้มแสง, ลักซ์"),
              ("voltage", "แรงดันที่ใช้", "3.3V-5V"),
              ("keys", "ชื่อค่าที่อ่านได้ (เฉพาะเซนเซอร์ ภาษาอังกฤษ คั่นด้วย ,)", "lux")]
    CODE = [("pins", "ขาของอุปกรณ์ บรรทัดละขา  ชื่อขา=ชนิด\nชนิดที่ใช้ได้: power5, power3, gnd, signal:out, signal:inp, signal:adc, signal:pwm, signal:i2c_sda, signal:i2c_scl",
             "VCC=power3\nGND=gnd\nSDA=signal:i2c_sda\nSCL=signal:i2c_scl"),
            ("imports", "import เพิ่มเติม บรรทัดละคำสั่ง (ถ้ามี)", ""),
            ("setup", "โค้ดตั้งค่า MicroPython ใช้ {ชื่อขา} แทนเลขขา เช่น {SDA} {SCL} {SIG}\nขา ADC ใช้ {ADC_SETUP_SIG} แล้วอ่านด้วย adc_SIG.read_u16()",
             "i2c = I2C(0, sda=Pin({SDA}), scl=Pin({SCL}))\ni2c.writeto(0x23, b'\\x10')"),
            ("read", "โค้ดอ่านค่า (เซนเซอร์) ต้องกำหนดตัวแปรตามชื่อค่าที่อ่านได้", "d = i2c.readfrom(0x23, 2)\nlux = round((d[0] << 8 | d[1]) / 1.2, 1)"),
            ("on", "โค้ดสั่งเปิด (อุปกรณ์สั่งงาน)", ""),
            ("off", "โค้ดสั่งปิด (อุปกรณ์สั่งงาน)", ""),
            ("explain_th", "คำอธิบายสั้น ๆ สำหรับนักเรียน", "วัดความสว่างเป็นหน่วยลักซ์ สื่อสารผ่าน I2C"),
            ("warnings", "คำเตือน บรรทัดละข้อ", "")]

    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("เพิ่มอุปกรณ์ใหม่ลงคลังความรู้")
        self.geometry("900x760")
        canvas = tk.Canvas(self, highlightthickness=0)
        sb = ttk.Scrollbar(self, command=canvas.yview)
        frm = ttk.Frame(canvas, padding=14)
        frm.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frm, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        ttk.Label(frm, text="ข้อความในช่องเป็นตัวอย่างเซนเซอร์ BH1750 แก้เป็นข้อมูลของอุปกรณ์ใหม่ได้เลย",
                  foreground="#5A6478").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self.v = {}
        r = 1
        for k, label, ex in self.FIELDS:
            ttk.Label(frm, text=label).grid(row=r, column=0, sticky="w", pady=3)
            e = ttk.Entry(frm, width=52, font=app.f)
            e.insert(0, ex)
            e.grid(row=r, column=1, sticky="w", padx=8)
            self.v[k] = e
            r += 1
        ttk.Label(frm, text="ชนิด").grid(row=r, column=0, sticky="w", pady=3)
        self.cmb_type = ttk.Combobox(frm, state="readonly", width=40,
                                     values=["sensor (เซนเซอร์ อ่านค่า)", "actuator (อุปกรณ์สั่งงาน)", "info (มีแค่ข้อมูล)"])
        self.cmb_type.current(0)
        self.cmb_type.grid(row=r, column=1, sticky="w", padx=8)
        r += 1
        for k, label, ex in self.CODE:
            ttk.Label(frm, text=label, wraplength=840, justify="left").grid(row=r, column=0, columnspan=2, sticky="w", pady=(10, 2))
            t = tk.Text(frm, height=4, width=94, font=app.fmono)
            t.insert("1.0", ex)
            t.grid(row=r + 1, column=0, columnspan=2, sticky="w")
            self.v[k] = t
            r += 2
        row = ttk.Frame(frm)
        row.grid(row=r, column=0, columnspan=2, sticky="w", pady=12)
        ttk.Button(row, text="🧪 ทดลองสร้างโค้ด", command=self.preview).pack(side="left")
        ttk.Button(row, text="💾 บันทึกลงคลังความรู้", style="Accent.TButton", command=self.save).pack(side="left", padx=8)
        ttk.Button(row, text="ยกเลิก", command=self.destroy).pack(side="left")

    def _get(self, k):
        w = self.v[k]
        return (w.get("1.0", "end") if isinstance(w, tk.Text) else w.get()).strip()

    def build(self):
        """อ่านฟอร์มเป็นข้อมูลอุปกรณ์ คืนค่า (comp, error)"""
        cid = re.sub(r"\W", "_", self._get("id").lower()).strip("_")
        if not cid:
            return None, "ใส่รหัสอุปกรณ์ก่อน"
        pins = []
        for line in self._get("pins").splitlines():
            if not line.strip():
                continue
            if "=" not in line:
                return None, "บรรทัดขาไม่ถูกรูปแบบ (ต้องเป็น ชื่อขา=ชนิด): " + line
            label, kind = [x.strip() for x in line.split("=", 1)]
            need = None
            if kind.startswith("signal"):
                kind, _, need = kind.partition(":")
                need = need.strip() or "out"
                if need not in ("out", "inp", "adc", "pwm", "i2c_sda", "i2c_scl", "touch"):
                    return None, "ชนิดสัญญาณไม่ถูกต้อง: " + line
            if kind not in ("power5", "power3", "gnd", "signal"):
                return None, "ชนิดขาไม่ถูกต้อง: " + line
            role = re.sub(r"\W", "_", label.upper()) if kind == "signal" else label
            pins.append(dict(label=label, kind=kind, need=need, role=role))
        if not any(p["kind"] == "signal" for p in pins):
            return None, "ต้องมีขาสัญญาณอย่างน้อย 1 ขา"
        ctype = self.cmb_type.get().split()[0]
        keywords = [k.strip().lower() for k in self._get("keywords").split(",") if k.strip()]
        if not keywords:
            return None, "ใส่คำที่นักเรียนอาจพิมพ์อย่างน้อย 1 คำ"
        comp = dict(id=cid, name_th=self._get("name_th"), name_en=self._get("name_en") or cid, category=self._get("category"),
                    type=ctype, keywords=keywords, voltage=self._get("voltage"), pins=pins,
                    explain_th=self._get("explain_th"), image="images/%s.jpg" % cid,
                    warnings=[w.strip() for w in self._get("warnings").splitlines() if w.strip()])
        imports = [l.strip() for l in self._get("imports").splitlines() if l.strip()]
        if imports:
            comp["imports"] = imports
        for k in ("setup", "read", "on", "off"):
            if self._get(k):
                comp[k] = self._get(k)
        if ctype == "sensor":
            comp["keys"] = [k.strip() for k in self._get("keys").split(",") if k.strip()]
            comp["sim"] = [0, 100, "float"]
            if not comp.get("read") or not comp["keys"]:
                return None, "เซนเซอร์ต้องมีโค้ดอ่านค่าและชื่อค่าที่อ่านได้"
            if not comp.get("setup"):
                return None, "เซนเซอร์ต้องมีโค้ดตั้งค่า"
        if ctype == "actuator" and not (comp.get("setup") and comp.get("on") and comp.get("off")):
            return None, "อุปกรณ์สั่งงานต้องมีโค้ดตั้งค่า สั่งเปิด และสั่งปิด"
        return comp, None

    def _trial(self, comp):
        """ทดลองสร้างโค้ดด้วยคลังความรู้ชั่วคราว คืนค่า (result, errors)"""
        board = self.app.board()
        if not board["micropython"]:
            board = self.app.kb.board_by_id["esp32-devkit"]
        kb = KnowledgeBase()
        kb.components = [c for c in kb.components if c["id"] != comp["id"]] + [comp]
        kb.reindex()
        res = CodeGenerator(kb).generate(("อ่าน " if comp["type"] == "sensor" else "") + comp["keywords"][0], board["id"])
        errs = list(res.errors)
        if comp["id"] not in [c["id"] for c in res.components]:
            errs.append("คำค้นแรก \"%s\" ไปตรงกับอุปกรณ์อื่น ให้ใช้คำที่เฉพาะเจาะจงกว่านี้" % comp["keywords"][0])
        if comp["type"] != "info":
            errs += check_code(res.code, board)[0]
        return res, errs

    def preview(self):
        comp, err = self.build()
        if err:
            messagebox.showerror("เพิ่มอุปกรณ์", err, parent=self)
            return
        res, errs = self._trial(comp)
        win = tk.Toplevel(self)
        win.title("ตัวอย่างโค้ดที่จะได้")
        t = tk.Text(win, font=self.app.fmono, width=90, height=30)
        t.pack(fill="both", expand=True)
        t.insert("1.0", ("✖ " + "\n✖ ".join(errs) + "\n\n" if errs else "✔ สร้างโค้ดได้\n\n") + res.code)

    def save(self):
        comp, err = self.build()
        if err:
            messagebox.showerror("เพิ่มอุปกรณ์", err, parent=self)
            return
        if comp["id"] in self.app.kb.comp_by_id and not messagebox.askyesno(
                "เพิ่มอุปกรณ์", "มีอุปกรณ์รหัสนี้อยู่แล้ว ต้องการแทนที่หรือไม่", parent=self):
            return
        _, errs = self._trial(comp)
        if errs:
            messagebox.showerror("เพิ่มอุปกรณ์", "ยังบันทึกไม่ได้ เพราะโค้ดที่ได้มีปัญหา:\n" + "\n".join(errs), parent=self)
            return
        self.app.kb.save_component(comp)
        self.app.reload_kb()
        messagebox.showinfo("เพิ่มอุปกรณ์", "เพิ่ม %s ลงคลังความรู้แล้ว\nพิมพ์คำสั่งที่มีคำว่า \"%s\" ได้เลย\n"
                            "กด \"เพิ่ม / เปลี่ยนรูป\" เพื่อใส่รูปของอุปกรณ์นี้" % (comp["name_th"], comp["keywords"][0]), parent=self)
        self.destroy()


def _log_error(exc, val, tb):
    import traceback
    text = "".join(traceback.format_exception(exc, val, tb))
    with open(os.path.join(BASE, "error_log.txt"), "a", encoding="utf-8") as f:
        f.write(text + "\n")
    messagebox.showerror("เกิดข้อผิดพลาด", "โปรแกรมพบข้อผิดพลาด บันทึกไว้ในไฟล์ error_log.txt\n\n" + text[-800:])


if __name__ == "__main__":
    root = tk.Tk()
    root.report_callback_exception = _log_error
    try:
        App(root)
    except Exception:
        import sys
        _log_error(*sys.exc_info())
        raise
    root.mainloop()

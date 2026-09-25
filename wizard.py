# -*- coding: utf-8 -*-
"""ผู้ช่วยนำทาง: พานักเรียนตั้งแต่เสียบบอร์ด จนอุปกรณ์จริงทำงาน

1 เชื่อมต่อบอร์ด  → ตรวจรุ่นบอร์ด MicroPython และอุปกรณ์ I2C ที่ต่ออยู่
2 อยากทำอะไร     → เลือกจากคลังโปรเจกต์ หรือพิมพ์เอง (ให้ AI ช่วยคิดได้)
3 เตรียมอุปกรณ์   → รายการของที่ต้องใช้ พร้อมรูป
4 ต่อสายทีละเส้น  → แอนิเมชันทีละเส้น นักเรียนต่อตามแล้วกดยืนยัน
5 ตรวจการต่อสาย   → ส่งโค้ดทดสอบไปรันบนบอร์ดจริงทีละอุปกรณ์
6 เขียนโค้ดและรัน → สร้างโค้ด รันบนบอร์ดจริง และดูการทำงานแบบเรียลไทม์
"""
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from device import DETECT_SCRIPT, parse_detect, parse_test, has_mpremote
from wiring import WiringCanvas

STEPS = ["เชื่อมต่อบอร์ด", "อยากทำอะไร", "เตรียมอุปกรณ์", "ต่อสายทีละเส้น", "ตรวจการต่อสาย", "เขียนโค้ดและรัน"]
EXTRA_PARTS = [("220Ω", "ตัวต้านทาน 220Ω"), ("4.7kΩ", "ตัวต้านทาน 4.7kΩ"), ("10kΩ", "ตัวต้านทาน 10kΩ"),
               ("1kΩ กับ 2kΩ", "ตัวต้านทาน 1kΩ และ 2kΩ (แบ่งแรงดัน)"), ("แหล่งจ่ายไฟแยก", "แหล่งจ่ายไฟแยก")]
STATUS = {"ok": ("✔ ผ่าน", "#1E8C5A"), "fail": ("✖ ไม่ผ่าน", "#C0392B"), "ask": ("❓ รอยืนยัน", "#D9661A"),
          "wait": ("… กำลังตรวจ", "#2457C5"), None: ("ยังไม่ได้ตรวจ", "#5A6478")}
LEVEL_COLOR = {"ง่าย": "#1E8C5A", "กลาง": "#D9661A", "ยาก": "#C0392B"}
BG = "#F4F7FB"


class ScrollFrame(ttk.Frame):
    """กรอบที่เลื่อนขึ้นลงได้ ใช้แสดงการ์ดโปรเจกต์จำนวนมาก"""

    def __init__(self, master, height=300):
        super().__init__(master)
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0, height=height)
        sb = ttk.Scrollbar(self, command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=BG)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._win, width=e.width))
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        for w in (self.canvas, self.inner):
            w.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._wheel))
            w.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _wheel(self, e):
        self.canvas.yview_scroll(int(-e.delta / 120) or (-1 if e.delta > 0 else 1), "units")


class WizardTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=10)
        self.app = app
        self.step = 0
        self.detected = None
        self.command = ""
        self.res = None
        self.test_status = {}
        self._poll_code = None
        self.f, self.fb, self.fbig = app.f, app.fb, app.fbig

        side = tk.Frame(self, bg="#FFFFFF", padx=10, pady=10, highlightbackground="#D9DFEA", highlightthickness=1)
        side.pack(side="left", fill="y")
        tk.Label(side, text="🧭 ผู้ช่วยนำทาง", font=self.fbig, bg="#FFFFFF", fg="#2457C5").pack(anchor="w", pady=(0, 10))
        self.step_labels = []
        for i, name in enumerate(STEPS):
            l = tk.Label(side, text="%d  %s" % (i + 1, name), font=self.f, bg="#FFFFFF", anchor="w",
                         padx=10, pady=8, width=17, cursor="hand2")
            l.pack(fill="x", pady=2)
            l.bind("<Button-1>", lambda e, n=i: self.go(n))
            self.step_labels.append(l)
        main = ttk.Frame(self)
        main.pack(side="left", fill="both", expand=True, padx=(12, 0))
        self.title = tk.Label(main, text="", font=(app.ff, 18, "bold"), anchor="w", bg=BG, fg="#1D2433")
        self.title.pack(fill="x")
        nav = ttk.Frame(main)
        nav.pack(side="bottom", fill="x")
        self.btn_back = ttk.Button(nav, text="◀ ย้อนกลับ", command=lambda: self.go(self.step - 1))
        self.btn_back.pack(side="left")
        self.btn_next = ttk.Button(nav, text="ขั้นต่อไป ▶", style="Accent.TButton", command=lambda: self.go(self.step + 1))
        self.btn_next.pack(side="right")
        self.body = ttk.Frame(main)
        self.body.pack(fill="both", expand=True, pady=10)
        self.go(0)

    # ---------------------------------------------------------------- ตัวช่วย
    def _clear(self):
        if self._poll_code:
            self.after_cancel(self._poll_code)
            self._poll_code = None
        for w in self.body.winfo_children():
            w.destroy()

    def _para(self, parent, text, **kw):
        l = tk.Label(parent, text=text, font=kw.pop("font", self.f), bg=kw.pop("bg", BG), fg=kw.pop("fg", "#1D2433"),
                     justify="left", anchor="w", wraplength=kw.pop("wrap", 920))
        l.pack(fill="x", anchor="w", pady=3)
        return l

    def _box(self, parent, text, bg="#FFF4CF", fg="#633806"):
        l = tk.Label(parent, text=text, font=self.f, bg=bg, fg=fg, justify="left", anchor="w", wraplength=900, padx=12, pady=8)
        l.pack(fill="x", pady=6)
        return l

    def board_changed(self):
        """ครูเปลี่ยนรุ่นบอร์ด: วางแผนขาใหม่ แล้ววาดขั้นปัจจุบันใหม่"""
        if self.command:
            self.res = self.app.gen.generate(self.command, self.app.board()["id"], self.app.cfg["app_name"])
            self.test_status = {}
            if self.step >= 1:
                self.go(self.step)

    def go(self, n):
        if n < 0 or n >= len(STEPS):
            return
        if n >= 2 and not (self.res and self.res.components):
            if self.step != 1:
                messagebox.showinfo("ผู้ช่วยนำทาง", "เลือกก่อนว่าอยากทำอะไร")
            n = 1
        self.step = n
        for i, l in enumerate(self.step_labels):
            if i == n:
                l.configure(bg="#2457C5", fg="#FFFFFF", font=self.fb)
            elif i < n:
                l.configure(bg="#DDF2E7", fg="#0F5C3A", font=self.f)
            else:
                l.configure(bg="#FFFFFF", fg="#5A6478", font=self.f)
        self.title.configure(text="ขั้นที่ %d: %s" % (n + 1, STEPS[n]))
        self.btn_back.configure(state="normal" if n > 0 else "disabled")
        self.btn_next.configure(state="normal" if n < len(STEPS) - 1 else "disabled")
        self._clear()
        [self.s_connect, self.s_goal, self.s_parts, self.s_wire, self.s_test, self.s_code][n]()

    # ================================================================ 1 เชื่อมต่อบอร์ด
    def s_connect(self):
        b = self.body
        self._para(b, "เสียบสาย USB ระหว่างบอร์ดกับคอมพิวเตอร์ แล้วกด \"ตรวจบอร์ด\" โปรแกรมจะดูว่าเป็นบอร์ดรุ่นไหน "
                      "มี MicroPython แล้วหรือยัง และมีอุปกรณ์ I2C เช่นจอ OLED ต่ออยู่หรือไม่", font=self.fbig)
        row = ttk.Frame(b)
        row.pack(fill="x", pady=10)
        ttk.Button(row, text="🔍 ตรวจบอร์ด", style="Accent.TButton", command=self._detect).pack(side="left")
        ttk.Button(row, text="ยังไม่มีบอร์ด ใช้โหมดจำลองไปก่อน ▶", command=lambda: self.go(1)).pack(side="left", padx=10)
        self.lbl_detect = tk.Label(b, text="ยังไม่ได้ตรวจ", font=self.f, bg="#FFFFFF", fg="#5A6478", justify="left",
                                   anchor="nw", padx=14, pady=12, wraplength=900)
        self.lbl_detect.pack(fill="x", pady=8)
        self._box(b, "ถ้าเป็นบอร์ดใหม่ ต้องลง MicroPython ก่อน 1 ครั้ง (ดู README ข้อ 2)\n"
                     "ถ้าเป็น Arduino Uno / Nano / Mega บอร์ดจะรัน Python ไม่ได้ แต่ยังใช้ผู้ช่วยนำทางดูการต่อสายและได้โค้ด C++ ได้",
                  "#EEF1F6", "#1D2433")
        if self.detected:
            self._show_detect(self.detected)

    def _detect(self):
        app = self.app
        app.refresh_ports()
        port = app.cmb_port.get()
        if not port:
            self.lbl_detect.configure(fg="#C0392B", text=(
                "ไม่พบพอร์ต USB\n• ตรวจว่าเสียบสาย USB แล้ว และเป็นสายที่ส่งข้อมูลได้ (สายชาร์จอย่างเดียวใช้ไม่ได้)\n"
                "• บางบอร์ดต้องติดตั้งไดรเวอร์ CP210x หรือ CH340 ก่อน"))
            return
        if not has_mpremote():
            self.lbl_detect.configure(fg="#C0392B", text="ต้องติดตั้ง mpremote ก่อน ดับเบิลคลิก install.bat อีกครั้ง")
            return
        self.lbl_detect.configure(fg="#2457C5", text="กำลังตรวจบอร์ดที่พอร์ต %s ..." % port)

        def work():
            ok, out = app.link.exec_code(port, DETECT_SCRIPT, timeout=20)
            self.after(0, lambda: self._detect_done(out))
        threading.Thread(target=work, daemon=True).start()

    def _detect_done(self, out):
        if not self.lbl_detect.winfo_exists():
            return
        info = parse_detect(out)
        if not info["mp"]:
            self.lbl_detect.configure(fg="#C0392B", text=(
                "คุยกับบอร์ดไม่ได้\n• ถ้าเป็นบอร์ดใหม่ ต้องลง MicroPython ก่อน\n"
                "• ถ้าเป็น Arduino Uno / Nano / Mega ให้เลือกรุ่นบอร์ดที่ช่องด้านบนเอง แล้วกดขั้นต่อไป\n"
                "• ปิดโปรแกรมอื่นที่ใช้พอร์ตอยู่ เช่น Thonny หรือ Arduino IDE\n\nรายละเอียด: " + out.strip()[-300:]))
            return
        self.detected = info
        if info["board_id"]:
            ids = [x["id"] for x in self.app.kb.boards]
            cur = self.app.board()["id"]
            # ถ้าครูเลือก KidBright32 ไว้แล้ว (ชิป ESP32 เหมือนกัน) ไม่ต้องเปลี่ยน
            if not (info["board_id"] == "esp32-devkit" and cur == "kidbright32"):
                self.app.cmb_board.current(ids.index(info["board_id"]))
                self.app._board_changed()
        self._show_detect(info)

    def _show_detect(self, info):
        board = self.app.board()
        lines = ["✔ เชื่อมต่อบอร์ดได้แล้ว", "เฟิร์มแวร์: %s" % info["mp"], "ชิป: %s" % info["machine"],
                 "รุ่นบอร์ดที่เลือกให้: %s  (ถ้าไม่ตรง เปลี่ยนได้ที่ช่องบอร์ดด้านบน)" % board["name"],
                 "หน่วยความจำว่าง: %s ไบต์" % info["free"], "ไฟล์บนบอร์ด: %s" % (", ".join(info["files"]) or "-")]
        if info["i2c"]:
            names = []
            for d in info["i2c"]:
                c = self.app.kb.comp_by_id.get(d["comp"]) if d["comp"] else None
                names.append("%s ที่อยู่ %s (ขา %s)" % (c["name_th"] if c else "อุปกรณ์ที่ยังไม่รู้จัก", hex(d["addr"]), d["pins"]))
            lines.append("พบอุปกรณ์ I2C: " + ", ".join(names))
        else:
            lines.append("ยังไม่พบอุปกรณ์ I2C (เซนเซอร์แบบอื่นตรวจได้ในขั้นที่ 5)")
        self.lbl_detect.configure(fg="#0F5C3A", text="\n".join(lines))

    # ================================================================ 2 อยากทำอะไร
    def s_goal(self):
        b = self.body
        self._para(b, "อยากให้อุปกรณ์ทำอะไร? เลือกจากคลังโปรเจกต์ หรือพิมพ์เป็นภาษาไทยเองก็ได้", font=self.fbig)
        row = ttk.Frame(b)
        row.pack(fill="x", pady=(2, 4))
        self.ent_goal = ttk.Entry(row, font=self.fbig)
        self.ent_goal.pack(side="left", fill="x", expand=True)
        if self.command:
            self.ent_goal.insert(0, self.command)
        self.ent_goal.bind("<Return>", lambda e: self._set_goal(self.ent_goal.get()))
        ttk.Button(row, text="ใช้คำสั่งนี้", style="Accent.TButton", command=lambda: self._set_goal(self.ent_goal.get())).pack(side="left", padx=6)
        self.btn_ai_goal = ttk.Button(row, text="🤖 ให้ AI ช่วยคิด", command=self._ai_goal)
        self.btn_ai_goal.pack(side="left")
        if not self.app.ai.available():
            self.btn_ai_goal.configure(state="disabled")
        self.lbl_goal = self._para(b, "", fg="#0F5C3A")
        if self.res and self.res.components:
            self._goal_summary()

        projects = self.app.kb.projects()
        filt = ttk.Frame(b)
        filt.pack(fill="x", pady=(6, 4))
        ttk.Label(filt, text="คลังโปรเจกต์ (%d)   หมวด:" % len(projects)).pack(side="left")
        cats = ["ทั้งหมด"] + sorted({p["category"] for p in projects})
        self.cmb_cat = ttk.Combobox(filt, values=cats, state="readonly", width=16)
        self.cmb_cat.set("ทั้งหมด")
        self.cmb_cat.pack(side="left", padx=6)
        ttk.Label(filt, text="ระดับ:").pack(side="left")
        self.cmb_lv = ttk.Combobox(filt, values=["ทั้งหมด", "ง่าย", "กลาง", "ยาก"], state="readonly", width=8)
        self.cmb_lv.set("ทั้งหมด")
        self.cmb_lv.pack(side="left", padx=6)
        ttk.Label(filt, text="ค้นหา:").pack(side="left")
        self.ent_find = ttk.Entry(filt, width=18)
        self.ent_find.pack(side="left", padx=6)
        for w in (self.cmb_cat, self.cmb_lv):
            w.bind("<<ComboboxSelected>>", lambda e: self._fill_projects())
        self.ent_find.bind("<KeyRelease>", lambda e: self._fill_projects())
        self.gallery = ScrollFrame(b, height=330)
        self.gallery.pack(fill="both", expand=True)
        self._fill_projects()

    def _fill_projects(self):
        inner = self.gallery.inner
        for w in inner.winfo_children():
            w.destroy()
        cat, lv, q = self.cmb_cat.get(), self.cmb_lv.get(), self.ent_find.get().strip().lower()
        detected = {d["comp"] for d in (self.detected or {}).get("i2c", []) if d.get("comp")}
        kb = self.app.kb
        shown = 0
        for p in kb.projects():
            if cat != "ทั้งหมด" and p["category"] != cat:
                continue
            if lv != "ทั้งหมด" and p["level"] != lv:
                continue
            parts = [kb.comp_by_id[c]["name_en"] for c in p["components"] if c in kb.comp_by_id]
            hay = (p["name_th"] + p["desc_th"] + p["command"] + " ".join(parts)).lower()
            if q and q not in hay:
                continue
            match = detected & set(p["components"])
            card = tk.Frame(inner, bg="#FFFFFF", cursor="hand2", padx=10, pady=8,
                            highlightbackground="#2457C5" if match else "#D9DFEA", highlightthickness=2)
            card.grid(row=shown // 3, column=shown % 3, sticky="nsew", padx=5, pady=5)
            top = tk.Frame(card, bg="#FFFFFF")
            top.pack(fill="x")
            ws = [tk.Label(top, text=p["emoji"] + "  " + p["name_th"], font=self.fb, bg="#FFFFFF", fg="#1D2433"),
                  tk.Label(top, text=p["level"], font=self.f, bg="#FFFFFF", fg=LEVEL_COLOR.get(p["level"], "#5A6478")),
                  tk.Label(card, text=p["desc_th"], font=self.f, bg="#FFFFFF", fg="#5A6478", anchor="w"),
                  tk.Label(card, text="ใช้: " + ", ".join(parts), font=self.f, bg="#FFFFFF", fg="#2457C5", anchor="w",
                           wraplength=280, justify="left")]
            ws[0].pack(side="left")
            ws[1].pack(side="right")
            for w in ws[2:]:
                w.pack(fill="x")
            if match:
                ws.append(tk.Label(card, text="✔ พบอุปกรณ์นี้ต่ออยู่กับบอร์ด", font=self.f, bg="#FFFFFF", fg="#1E8C5A", anchor="w"))
                ws[-1].pack(fill="x")
            for w in [card, top] + ws:
                w.bind("<Button-1>", lambda e, c=p["command"]: self._set_goal(c))
            shown += 1
        for i in range(3):
            inner.columnconfigure(i, weight=1, uniform="c")
        if not shown:
            tk.Label(inner, text="ไม่พบโปรเจกต์ที่ตรงกับตัวกรอง", font=self.f, bg=BG, fg="#5A6478").grid(row=0, column=0, sticky="w")

    def _set_goal(self, cmd):
        cmd = cmd.strip()
        if not cmd:
            return
        self.command = cmd
        if self.ent_goal.winfo_exists():
            self.ent_goal.delete(0, "end")
            self.ent_goal.insert(0, cmd)
        self.res = self.app.gen.generate(cmd, self.app.board()["id"], self.app.cfg["app_name"])
        self.test_status = {}
        if not self.res.components:
            self.lbl_goal.configure(fg="#C0392B", text="ยังไม่รู้ว่าต้องใช้อุปกรณ์อะไร ลองระบุชื่ออุปกรณ์ในคำสั่ง หรือกด \"ให้ AI ช่วยคิด\"")
            return
        self._goal_summary()

    def _goal_summary(self):
        names = ", ".join(c["name_th"] for c in self.res.components)
        txt = "✔ ต้องใช้: %s   → กด \"ขั้นต่อไป\" เพื่อเตรียมอุปกรณ์" % names
        if self.res.errors:
            txt += "\n✖ " + "\n✖ ".join(self.res.errors)
        self.lbl_goal.configure(fg="#C0392B" if self.res.errors else "#0F5C3A", text=txt)

    def _ai_goal(self):
        goal = self.ent_goal.get().strip()
        if not goal:
            self.lbl_goal.configure(fg="#C0392B", text="พิมพ์ก่อนว่าอยากทำอะไร เช่น \"อยากให้ต้นไม้รดน้ำเอง\"")
            return
        self.lbl_goal.configure(fg="#2457C5", text="AI กำลังคิดว่าต้องใช้อุปกรณ์อะไร...")
        app = self.app

        def work():
            try:
                out = app.ai.suggest_project(goal, app.kb, app.board(), self.detected)
                self.after(0, lambda: self._ai_goal_done(out))
            except Exception as e:  # noqa: BLE001
                msg = "เชื่อมต่อ AI ไม่ได้: %s" % e
                self.after(0, lambda: self.lbl_goal.winfo_exists() and self.lbl_goal.configure(fg="#C0392B", text=msg))
        threading.Thread(target=work, daemon=True).start()

    def _ai_goal_done(self, out):
        if not self.lbl_goal.winfo_exists():
            return
        self._set_goal(out.get("command", ""))
        if out.get("reason"):
            self.lbl_goal.configure(text=self.lbl_goal.cget("text") + "\nAI แนะนำ: " + out["reason"])

    # ================================================================ 3 เตรียมอุปกรณ์
    def s_parts(self):
        b = self.body
        self._box(b, "⚠ ถอดสาย USB ออกจากคอมพิวเตอร์ก่อนต่อสายทุกครั้ง เพื่อไม่ให้บอร์ดหรืออุปกรณ์เสียหาย", "#FCE9DA", "#7A3510")
        board = self.app.board()
        wrap = tk.Frame(b, bg=BG)
        wrap.pack(fill="x")
        items = [(board, board["name"], "บอร์ด")] + [(c, c["name_th"], c["name_en"]) for c in self.res.components]
        self._thumbs = []
        for i, (it, name, sub) in enumerate(items):
            card = tk.Frame(wrap, bg="#FFFFFF", highlightbackground="#D9DFEA", highlightthickness=1, padx=8, pady=8)
            card.grid(row=i // 4, column=i % 4, padx=5, pady=5, sticky="nsew")
            img = self.app.load_thumb(it, 150)
            self._thumbs.append(img)
            if img:
                tk.Label(card, image=img, bg="#FFFFFF").pack()
            else:
                tk.Label(card, text="(ยังไม่มีรูป)\nเพิ่มได้ที่แท็บคลังความรู้", bg="#F1EFE8", fg="#888780",
                         width=20, height=5, font=self.f).pack()
            v = tk.BooleanVar()
            tk.Checkbutton(card, text=name[:26], variable=v, bg="#FFFFFF", font=self.fb, anchor="w").pack(anchor="w")
            tk.Label(card, text=sub, bg="#FFFFFF", fg="#5A6478", font=self.f).pack(anchor="w")
        extras = ["สายจัมเปอร์ %d เส้น" % max(1, len(self.res.wiring)), "เบรดบอร์ด 1 แผ่น", "สาย USB ที่ส่งข้อมูลได้"]
        alltext = " ".join(self.res.warnings)
        extras += [label for key, label in EXTRA_PARTS if key in alltext]
        self._para(b, "อุปกรณ์เสริม: " + ", ".join(extras), font=self.fb)
        if self.res.warnings:
            self._para(b, "ข้อควรระวัง:\n" + "\n".join("⚠ " + w for w in self.res.warnings), fg="#9A4A10")

    # ================================================================ 4 ต่อสายทีละเส้น
    def s_wire(self):
        b = self.body
        self.cap = tk.Label(b, text="", font=self.fbig, bg="#E4ECFB", fg="#1D2433", anchor="w", justify="left",
                            padx=12, pady=10, wraplength=920)
        self.cap.pack(fill="x")
        row = ttk.Frame(b)
        row.pack(fill="x", pady=6)
        ttk.Button(row, text="◀ เส้นก่อนหน้า", command=self._wire_back).pack(side="left")
        self.btn_wire = ttk.Button(row, text="", style="Accent.TButton", command=self._wire_next)
        self.btn_wire.pack(side="left", padx=8)
        ttk.Button(row, text="ดูแอนิเมชันทุกเส้นก่อน", command=lambda: (self.wc.reset(), self.wc.play(), self._wire_btn())).pack(side="left")
        ttk.Button(row, text="เริ่มต่อใหม่", command=lambda: (self.wc.reset(), self._wire_btn())).pack(side="left", padx=8)
        frame = ttk.Frame(b)
        frame.pack(fill="both", expand=True)
        self.wc = WiringCanvas(frame, font_family=self.app.ff, on_caption=self._wire_caption, height=440)
        sb = ttk.Scrollbar(frame, command=self.wc.yview)
        self.wc.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.wc.pack(side="left", fill="both", expand=True)
        self.wc.load(self.res, self.app.board())
        self._wire_btn()

    def _wire_caption(self, text, step, total):
        if self.cap.winfo_exists():
            self.cap.configure(text="👀 " + ("[%d/%d] " % (step, total) if step else "") + text)
            if hasattr(self, "btn_wire") and self.btn_wire.winfo_exists():
                self._wire_btn()

    def _wire_btn(self):
        n, s = len(self.wc.paths), self.wc.step
        if n == 0:
            txt = "ไม่ต้องต่อสาย ไปขั้นต่อไปได้เลย ▶"
        elif s == 0:
            txt = "▶ เริ่มต่อเส้นที่ 1"
        elif s < n:
            txt = "✔ ต่อเส้นที่ %d เสร็จแล้ว → เส้นที่ %d" % (s, s + 1)
        else:
            txt = "✔ ต่อครบ %d เส้นแล้ว → ไปตรวจสาย" % n
        self.btn_wire.configure(text=txt)

    def _wire_next(self):
        n, s = len(self.wc.paths), self.wc.step
        if s >= n:
            if n:
                messagebox.showinfo("ต่อครบแล้ว", "ตรวจอีกครั้งว่าไม่มีสายหลวม แล้วเสียบสาย USB กลับเข้าคอมพิวเตอร์")
            self.go(4)
            return
        self.wc.next_step(True, self.wc.focus_current)
        self._wire_btn()

    def _wire_back(self):
        self.wc.prev_step()
        self.wc.focus_current()
        self._wire_btn()

    # ================================================================ 5 ตรวจการต่อสาย
    def s_test(self):
        b = self.body
        self._para(b, "โปรแกรมจะส่งโค้ดทดสอบสั้น ๆ ไปรันบนบอร์ดจริงทีละอุปกรณ์ เพื่อดูว่าต่อสายถูกหรือไม่ "
                      "ระหว่างตรวจเซนเซอร์ ให้ลองกระตุ้นมันด้วย เช่น กดปุ่ม โบกมือหน้า PIR หรือบังเซนเซอร์แสง", font=self.fbig)
        if not self.app.cmb_port.get() or not self.app.board()["micropython"]:
            self._box(b, "ยังไม่ได้ต่อบอร์ดที่รัน MicroPython จึงตรวจสายจริงไม่ได้ ข้ามไปขั้นต่อไปแล้วใช้โหมดจำลองได้", "#EEF1F6", "#1D2433")
        ttk.Button(b, text="🔌 ตรวจทุกอุปกรณ์", style="Accent.TButton", command=self._test_all).pack(anchor="w", pady=6)
        self.test_rows = {}
        box = tk.Frame(b, bg="#FFFFFF", padx=10, pady=6)
        box.pack(fill="x")
        for c in self.res.components:
            row = tk.Frame(box, bg="#FFFFFF")
            row.pack(fill="x", pady=4)
            tk.Label(row, text=c["name_th"][:34], font=self.fb, bg="#FFFFFF", width=34, anchor="w").pack(side="left")
            st = tk.Label(row, text="", font=self.fb, bg="#FFFFFF", width=13, anchor="w")
            st.pack(side="left")
            ttk.Button(row, text="ตรวจ", command=lambda c=c: self._test_one(c)).pack(side="left", padx=6)
            msg = tk.Label(row, text="", font=self.f, bg="#FFFFFF", fg="#5A6478", anchor="w", justify="left", wraplength=470)
            msg.pack(side="left", fill="x")
            self.test_rows[c["id"]] = (st, msg)
            self._set_status(c["id"], *self.test_status.get(c["id"], (None, "")))
        self._para(b, "ถ้าไม่ผ่าน: ถอด USB → กลับไปขั้นที่ 4 ดูสายของอุปกรณ์นั้นอีกครั้ง → เสียบ USB → กดตรวจใหม่", fg="#5A6478")

    def _set_status(self, cid, status, msg=""):
        self.test_status[cid] = (status, msg)
        row = getattr(self, "test_rows", {}).get(cid)
        if row and row[0].winfo_exists():
            text, color = STATUS[status]
            row[0].configure(text=text, fg=color)
            row[1].configure(text=msg)

    def _can_test(self):
        app = self.app
        if not app.cmb_port.get():
            messagebox.showinfo("ตรวจสาย", "ยังไม่ได้เลือกพอร์ต USB เสียบบอร์ดแล้วกด 'ค้นหาพอร์ต'")
            return False
        if not app.board()["micropython"]:
            messagebox.showinfo("ตรวจสาย", "บอร์ดนี้รัน MicroPython ไม่ได้ จึงตรวจอัตโนมัติไม่ได้ ให้ตรวจด้วยตาเทียบกับภาพในขั้นที่ 4")
            return False
        if not has_mpremote():
            messagebox.showinfo("ตรวจสาย", "ต้องติดตั้ง mpremote ก่อน ดับเบิลคลิก install.bat อีกครั้ง")
            return False
        return True

    def _test_one(self, comp, then=None):
        if not self._can_test():
            return
        self._set_status(comp["id"], "wait", "ทดสอบบนบอร์ดจริง...")
        code = self.app.gen.test_code(comp, self.res.assigned.get(comp["id"], {}), self.app.board())
        port = self.app.cmb_port.get()

        def work():
            ok, out = self.app.link.exec_code(port, code, timeout=30)
            self.after(0, lambda: self._test_done(comp, out, then))
        threading.Thread(target=work, daemon=True).start()

    def _test_done(self, comp, out, then):
        status, msg = parse_test(out)
        if status == "ask":
            yes = messagebox.askyesno("ตรวจด้วยตา", msg + "\n\nกด Yes ถ้าทำงานถูกต้อง")
            status, msg = ("ok", "ยืนยันด้วยตาแล้ว") if yes else ("fail", "ไม่ทำงาน ตรวจสายสัญญาณ ไฟเลี้ยง และ GND")
        self._set_status(comp["id"], status, msg)
        if then:
            then()

    def _test_all(self):
        if not self._can_test():
            return
        comps = list(self.res.components)

        def chain(i=0):
            if i < len(comps):
                self._test_one(comps[i], lambda: chain(i + 1))
            elif all(self.test_status.get(c["id"], (None,))[0] == "ok" for c in comps):
                messagebox.showinfo("ตรวจสาย", "ต่อสายถูกต้องทุกอุปกรณ์ ✔ ไปเขียนโค้ดกันเลย")
        chain()

    # ================================================================ 6 เขียนโค้ดและรัน
    def s_code(self):
        b = self.body
        app = self.app
        app.txt_cmd.delete("1.0", "end")
        app.txt_cmd.insert("1.0", self.command)
        app.generate()
        self._para(b, "คำสั่ง: " + self.command, font=self.fb)
        row = ttk.Frame(b)
        row.pack(fill="x", pady=6)
        ttk.Button(row, text="▶ รันบนบอร์ดจริง", style="Accent.TButton", command=app.run_board).pack(side="left")
        ttk.Button(row, text="⬆ บันทึกลงบอร์ด (main.py)", command=app.upload_board).pack(side="left", padx=6)
        ttk.Button(row, text="⚡ ดูการทำงานแบบจำลอง",
                   command=lambda: (app.nb.select(app.tab_index["live"]), app.start_sim())).pack(side="left")
        ttk.Button(row, text="✏ แก้โค้ดเพิ่ม", command=lambda: app.nb.select(app.tab_index["code"])).pack(side="left", padx=6)
        if any(c.get("library") for c in self.res.components):
            ttk.Button(row, text="📦 ติดตั้งไลบรารีลงบอร์ด", command=app.install_libs).pack(side="left")
        fr = ttk.Frame(b)
        fr.pack(fill="both", expand=True)
        self.code_view = tk.Text(fr, font=app.fmono, bg="#FBFCFE", relief="flat", padx=10, pady=8, height=16)
        sb = ttk.Scrollbar(fr, command=self.code_view.yview)
        self.code_view.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.code_view.pack(side="left", fill="both", expand=True)
        self._para(b, "กด \"รันบนบอร์ดจริง\" แล้วโปรแกรมจะพาไปแท็บข้อมูลเรียลไทม์ ดูตัวเลข กราฟ และภาพจุดข้อมูลวิ่งบนสาย "
                      "ถ้าเปิด \"ใช้ AI ช่วยสร้างโค้ด\" ไว้ด้านบน โค้ดจะมาจาก AI และโปรแกรมตรวจเลขขาซ้ำให้อีกครั้ง", fg="#5A6478")
        self._sync_code()

    def _sync_code(self):
        if not self.code_view.winfo_exists():
            return
        code = self.app.txt_code.get("1.0", "end")
        if code != self.code_view.get("1.0", "end"):
            self.code_view.delete("1.0", "end")
            self.code_view.insert("1.0", code)
        self._poll_code = self.after(800, self._sync_code)

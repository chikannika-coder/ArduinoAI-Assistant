# -*- coding: utf-8 -*-
"""หน้าต่าง "เพิ่มอุปกรณ์ใหม่ / แก้ไขอุปกรณ์" ของคลังความรู้

ครูแนบรูป (รูปถ่ายอุปกรณ์ ผังขา หน้าร้านค้า) หรือข้อความ (โค้ด Arduino, datasheet, ไฟล์ Word) ได้
แล้วกดให้ AI วิเคราะห์ AI จะอธิบายการทำงาน และกรอกฟอร์มตามรูปแบบของโปรแกรมให้
โปรแกรมทดลองสร้างโค้ดทุกครั้งก่อนบันทึก ถ้าโค้ดผิดจะให้ AI แก้เองอีก 1 รอบ
"""
import json
import os
import queue
import re
import tempfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from kb import KnowledgeBase, BASE
from generator import CodeGenerator, check_code
from analyzer import (read_attachment, image_b64, build_prompt, parse_ai_reply, offline_analyze,
                      IMAGE_EXT, TEXT_EXT, MAX_IMAGES)

IMAGES = os.path.join(BASE, "images")
KINDS = ("power5", "power3", "gnd", "signal")
NEEDS = ("out", "inp", "adc", "pwm", "i2c_sda", "i2c_scl", "touch")
C = dict(ink="#1D2433", muted="#5A6478", blue="#2457C5", green="#1E8C5A", orange="#D9661A", red="#C0392B", soft="#EEF3FC")


def _derived_role(label):
    return re.sub(r"\W", "_", label.upper())


class NewComponentDialog(tk.Toplevel):
    """ฟอร์มเพิ่มหรือแก้ไขอุปกรณ์ในคลังความรู้ (บันทึกลง knowledge/components.json)"""
    FIELDS = [("id", "รหัสอุปกรณ์ (ภาษาอังกฤษ ไม่มีช่องว่าง)", "bh1750"),
              ("name_th", "ชื่อภาษาไทย", "เซนเซอร์วัดความเข้มแสง BH1750"),
              ("name_en", "ชื่อภาษาอังกฤษ", "BH1750"),
              ("category", "หมวด", "แสง"),
              ("keywords", "คำที่นักเรียนอาจพิมพ์ (คั่นด้วย ,) ใส่คำแรกเป็นคำเฉพาะของอุปกรณ์", "bh1750, ความเข้มแสง, ลักซ์"),
              ("voltage", "แรงดันที่ใช้", "3.3V-5V"),
              ("keys", "ชื่อค่าที่อ่านได้ (เฉพาะเซนเซอร์ ภาษาอังกฤษ คั่นด้วย ,)", "lux"),
              ("sim", "ช่วงค่าสำหรับโหมดจำลอง  ต่ำสุด, สูงสุด  (เปิด/ปิดใส่ 0, 1, bool)", "0, 2000"),
              ("i2c_addr", "ที่อยู่ I2C (ถ้ามี คั่นด้วย ,) ใช้ตอนตรวจสาย", "0x23"),
              ("library", "ไลบรารีที่ต้องติดตั้งบนบอร์ด (ถ้ามี) เช่น ssd1306", "")]
    CODE = [("pins", "ขาของอุปกรณ์ บรรทัดละขา  ชื่อขา=ชนิด   (ถ้าต้องการตั้งชื่อในโค้ดเอง เติม @ชื่อ เช่น AO=signal:adc@SIG)\n"
                     "ชนิดที่ใช้ได้: power5, power3, gnd, signal:out, signal:inp, signal:adc, signal:pwm, signal:i2c_sda, signal:i2c_scl",
             "VCC=power3\nGND=gnd\nSDA=signal:i2c_sda\nSCL=signal:i2c_scl"),
            ("imports", "import เพิ่มเติม บรรทัดละคำสั่ง (ถ้ามี)", ""),
            ("setup", "โค้ดตั้งค่า MicroPython ใช้ {ชื่อขา} แทนเลขขา เช่น {SDA} {SCL} {SIG}\nขา ADC ใช้ {ADC_SETUP_SIG} แล้วอ่านด้วย adc_SIG.read_u16()",
             "i2c = I2C(0, sda=Pin({SDA}), scl=Pin({SCL}))\ni2c.writeto(0x23, b'\\x10')"),
            ("helpers", "ฟังก์ชันช่วย (ถ้ามี) ห้ามใช้ {ชื่อขา} ในส่วนนี้ ให้สร้างตัวแปรไว้ในโค้ดตั้งค่าก่อน", ""),
            ("read", "โค้ดอ่านค่า (เซนเซอร์) ต้องกำหนดตัวแปรตามชื่อค่าที่อ่านได้", "d = i2c.readfrom(0x23, 2)\nlux = round((d[0] << 8 | d[1]) / 1.2, 1)"),
            ("on", "โค้ดสั่งเปิด (อุปกรณ์สั่งงาน)", ""),
            ("off", "โค้ดสั่งปิด (อุปกรณ์สั่งงาน)", ""),
            ("explain_th", "คำอธิบายสั้น ๆ สำหรับนักเรียน", "วัดความสว่างเป็นหน่วยลักซ์ สื่อสารผ่าน I2C"),
            ("warnings", "คำเตือน บรรทัดละข้อ", "")]
    TYPES = ["sensor (เซนเซอร์ อ่านค่า)", "actuator (อุปกรณ์สั่งงาน)", "info (มีแค่ข้อมูล)"]

    def __init__(self, app, comp=None):
        super().__init__(app.root)
        self.app = app
        self.editing = comp
        self.attach = []             # รูปที่แนบ (รูปแรก = รูปหลักของอุปกรณ์)
        self._thumbs = []
        self.analysis = (comp or {}).get("ai_analysis_th", "")
        self.q = queue.Queue()
        self.busy = False
        self.title("แก้ไขอุปกรณ์: " + comp["name_th"] if comp else "เพิ่มอุปกรณ์ใหม่ลงคลังความรู้")
        self.geometry("980x860")
        self.minsize(820, 600)
        canvas = tk.Canvas(self, highlightthickness=0)
        sb = ttk.Scrollbar(self, command=canvas.yview)
        frm = ttk.Frame(canvas, padding=14)
        frm.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frm, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        self.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))
        self.bind("<Button-4>", lambda e: canvas.yview_scroll(-3, "units"))
        self.bind("<Button-5>", lambda e: canvas.yview_scroll(3, "units"))
        self._build_attach(frm)
        self._build_form(frm)
        if comp:
            self.fill(comp)
            p = app.kb.image_path(comp)
            for x in [p] + [os.path.join(BASE, g) for g in comp.get("gallery", [])]:
                if x and os.path.exists(x):
                    self.attach.append(x)
            if comp.get("notes_th"):
                self.txt_src.insert("1.0", comp["notes_th"])
            if self.analysis:
                self._show_analysis(self.analysis)
            self._refresh_thumbs()
        self.after(100, self._poll)

    # ================================================================ ส่วนที่ 1: แนบรูป / ข้อความ ให้ AI วิเคราะห์
    def _build_attach(self, frm):
        app = self.app
        box = ttk.LabelFrame(frm, text="① แนบรูปหรือข้อความ แล้วให้ AI วิเคราะห์  (ไม่บังคับ)", padding=10)
        box.grid(row=0, column=0, columnspan=2, sticky="we", pady=(0, 12))
        ttk.Label(box, foreground=C["muted"], wraplength=900, justify="left", text=(
            "แนบรูปถ่ายอุปกรณ์ รูปผังขา (pinout) หน้าร้านค้าออนไลน์ หรือวางข้อความ เช่น โค้ดตัวอย่าง Arduino, ข้อมูลจาก datasheet, "
            "ไฟล์ Word/.ino/.txt แล้วกดปุ่ม AI  โปรแกรมจะอธิบายการทำงาน และกรอกฟอร์มด้านล่างให้ตามรูปแบบที่สร้างโค้ดได้")).pack(anchor="w")
        row = ttk.Frame(box)
        row.pack(fill="x", pady=(8, 4))
        ttk.Button(row, text="🖼 เพิ่มรูป", command=self.add_images).pack(side="left")
        ttk.Button(row, text="📋 วางรูปจากคลิปบอร์ด", command=self.paste_image).pack(side="left", padx=6)
        ttk.Button(row, text="📄 เปิดไฟล์ข้อความ / โค้ด / Word", command=self.add_text_file).pack(side="left")
        ttk.Button(row, text="ล้างทั้งหมด", command=self.clear_attach).pack(side="left", padx=6)
        self.thumb_row = tk.Frame(box, bg=C["soft"], height=110)
        self.thumb_row.pack(fill="x", pady=4)
        ttk.Label(box, text="ข้อความประกอบ (พิมพ์หรือวางได้เลย):").pack(anchor="w", pady=(6, 2))
        tf = ttk.Frame(box)
        tf.pack(fill="x")
        self.txt_src = tk.Text(tf, height=8, width=110, font=app.fmono, wrap="word", undo=True)
        sb = ttk.Scrollbar(tf, command=self.txt_src.yview)
        self.txt_src.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.txt_src.pack(side="left", fill="x", expand=True)
        row2 = ttk.Frame(box)
        row2.pack(fill="x", pady=(8, 4))
        self.btn_ai = ttk.Button(row2, text="🤖 ให้ AI วิเคราะห์และกรอกฟอร์ม", style="Accent.TButton", command=self.ai_analyze)
        self.btn_ai.pack(side="left")
        ttk.Button(row2, text="🔎 วิเคราะห์แบบไม่ใช้ AI (จากโค้ด)", command=self.offline).pack(side="left", padx=6)
        self.lbl_state = ttk.Label(row2, text="", foreground=C["muted"])
        self.lbl_state.pack(side="left", padx=10)
        if not app.ai.available():
            self.lbl_state.configure(text="ยังไม่ได้เปิด AI (ตั้งค่าได้ที่แท็บ ⚙ ตั้งค่า) ใช้ปุ่มวิเคราะห์แบบไม่ใช้ AI ได้")
        ttk.Label(box, text="ผลการวิเคราะห์:").pack(anchor="w", pady=(6, 2))
        rf = ttk.Frame(box)
        rf.pack(fill="x")
        self.txt_res = tk.Text(rf, height=10, width=110, font=app.f, wrap="word", bg="#FBFCFE")
        sb2 = ttk.Scrollbar(rf, command=self.txt_res.yview)
        self.txt_res.configure(yscrollcommand=sb2.set)
        sb2.pack(side="right", fill="y")
        self.txt_res.pack(side="left", fill="x", expand=True)
        for tag, color in (("err", C["red"]), ("ok", C["green"]), ("h", C["blue"]), ("warn", C["orange"])):
            self.txt_res.tag_configure(tag, foreground=color, font=app.fb if tag == "h" else app.f)
        self.txt_res.insert("1.0", "(ยังไม่ได้วิเคราะห์)")
        self.txt_res.configure(state="disabled")

    def _refresh_thumbs(self):
        for w in self.thumb_row.winfo_children():
            w.destroy()
        self._thumbs = []
        if not self.attach:
            tk.Label(self.thumb_row, text="ยังไม่มีรูป  (รูปแรกจะเป็นรูปหลักของอุปกรณ์ในคลังความรู้)", bg=C["soft"],
                     fg=C["muted"], font=self.app.f).pack(side="left", padx=10, pady=30)
            return
        for i, p in enumerate(self.attach):
            cell = tk.Frame(self.thumb_row, bg=C["soft"])
            cell.pack(side="left", padx=4, pady=4)
            img = self._thumb(p, 90)
            self._thumbs.append(img)
            lbl = tk.Label(cell, image=img, text="" if img else os.path.basename(p)[:12], bg="#FFFFFF",
                           width=None if img else 12, height=None if img else 5, relief="solid", bd=1, cursor="hand2")
            lbl.pack()
            lbl.bind("<Button-1>", lambda e, i=i: self._remove(i))
            tk.Label(cell, text=("รูปหลัก" if i == 0 else "รูป %d" % (i + 1)) + " ✖", bg=C["soft"], fg=C["muted"],
                     font=(self.app.ff, 9)).pack()
        tk.Label(self.thumb_row, text="คลิกรูปเพื่อเอาออก\nส่งให้ AI ได้สูงสุด %d รูป" % MAX_IMAGES, bg=C["soft"],
                 fg=C["muted"], font=(self.app.ff, 9), justify="left").pack(side="left", padx=8)

    def _thumb(self, path, size):
        try:
            from PIL import Image, ImageTk, ImageOps
            im = ImageOps.exif_transpose(Image.open(path))
            im.thumbnail((size, size))
            return ImageTk.PhotoImage(im, master=self)
        except Exception:  # noqa: BLE001
            try:
                img = tk.PhotoImage(file=path, master=self)
                f = max(1, img.width() // size)
                return img.subsample(f, f)
            except tk.TclError:
                return None

    def _remove(self, i):
        if 0 <= i < len(self.attach):
            self.attach.pop(i)
            self._refresh_thumbs()

    def add_images(self):
        paths = filedialog.askopenfilenames(parent=self, filetypes=[("รูปภาพ", " ".join("*" + e for e in IMAGE_EXT)), ("ทุกไฟล์", "*.*")])
        for p in paths:
            if p not in self.attach:
                self.attach.append(p)
        self._refresh_thumbs()

    def paste_image(self):
        try:
            from PIL import ImageGrab
            data = ImageGrab.grabclipboard()
        except Exception as e:  # noqa: BLE001
            messagebox.showinfo("วางรูป", "วางรูปจากคลิปบอร์ดไม่ได้ในเครื่องนี้ (%s)\nให้บันทึกรูปเป็นไฟล์แล้วกด \"เพิ่มรูป\" แทน" % e, parent=self)
            return
        if isinstance(data, list):
            self.attach += [p for p in data if str(p).lower().endswith(IMAGE_EXT)]
        elif data is not None:
            path = os.path.join(tempfile.mkdtemp(prefix="arduinoai_clip_"), "clipboard.png")
            data.save(path)
            self.attach.append(path)
        else:
            messagebox.showinfo("วางรูป", "ในคลิปบอร์ดไม่มีรูป ลองคลิกขวาที่รูปแล้วเลือก \"คัดลอกรูป\" ก่อน", parent=self)
            return
        self._refresh_thumbs()

    def add_text_file(self):
        exts = " ".join("*" + e for e in TEXT_EXT + (".docx",))
        path = filedialog.askopenfilename(parent=self, filetypes=[("ข้อความ / โค้ด / Word", exts), ("ทุกไฟล์", "*.*")])
        if not path:
            return
        try:
            text, imgs = read_attachment(path)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("เปิดไฟล์", "อ่านไฟล์ไม่ได้: %s" % e, parent=self)
            return
        if text.strip():
            if self.txt_src.get("1.0", "end").strip():
                self.txt_src.insert("end", "\n\n")
            self.txt_src.insert("end", "----- จากไฟล์ %s -----\n%s\n" % (os.path.basename(path), text.strip()))
        if imgs:
            n = min(len(imgs), MAX_IMAGES)
            if messagebox.askyesno("รูปในเอกสาร", "พบรูปในเอกสาร %d รูป ต้องการแนบ %d รูปแรกให้ AI ดูด้วยหรือไม่" % (len(imgs), n), parent=self):
                self.attach += imgs[:n]
                self._refresh_thumbs()
        self.lbl_state.configure(text="เพิ่มข้อความจาก %s แล้ว" % os.path.basename(path))

    def clear_attach(self):
        self.attach = []
        self.txt_src.delete("1.0", "end")
        self._refresh_thumbs()

    def _show_analysis(self, text, extra=None):
        t = self.txt_res
        t.configure(state="normal")
        t.delete("1.0", "end")
        for line in text.strip().splitlines():
            s = line.strip()
            if s.startswith("#"):
                t.insert("end", s.lstrip("# ") + "\n", "h")
            else:
                t.insert("end", line.replace("**", "") + "\n")
        for tag, line in (extra or []):
            t.insert("end", line + "\n", tag)
        t.configure(state="disabled")

    # ---------- AI
    def ai_analyze(self):
        if self.busy:
            return
        if not self.app.ai.available():
            if messagebox.askyesno("AI", "ยังไม่ได้เปิด AI ในแท็บ ⚙ ตั้งค่า\nต้องการวิเคราะห์แบบไม่ใช้ AI (อ่านจากโค้ด) แทนหรือไม่", parent=self):
                self.offline()
            return
        text = self.txt_src.get("1.0", "end").strip()
        if not text and not self.attach:
            messagebox.showinfo("AI", "แนบรูป หรือพิมพ์/วางข้อความเกี่ยวกับอุปกรณ์ก่อน", parent=self)
            return
        images, skipped = [], []
        for p in self.attach[:MAX_IMAGES]:
            try:
                images.append(image_b64(p))
            except Exception as e:  # noqa: BLE001
                skipped.append("%s (%s)" % (os.path.basename(p), e))
        form = None
        if self.editing:
            comp, _ = self.build(strict=False)
            form = json.dumps(comp, ensure_ascii=False, indent=1) if comp else None
        self._start_ai(text, images, form, None, skipped)

    def _start_ai(self, text, images, form, fix_errors, skipped=None):
        self.busy = True
        self.btn_ai.configure(state="disabled")
        self.lbl_state.configure(text="⏳ AI กำลังวิเคราะห์%s... (อาจใช้เวลา 20-60 วินาที)" % (" รูป %d รูปและข้อความ" % len(images) if images else ""))
        board = self.app.board()
        kb = self.app.kb
        self._last = (text, images)

        def work():
            try:
                prompt = build_prompt(text, kb, board, form, len(images), fix_errors)
                reply, note = self.app.ai.chat_with_images(prompt, images)
                analysis, comp = parse_ai_reply(reply)
                self.q.put(("ai", analysis, comp, note, bool(fix_errors), skipped or []))
            except Exception as e:  # noqa: BLE001
                self.q.put(("ai_fail", str(e)))
        threading.Thread(target=work, daemon=True).start()

    def _poll(self):
        try:
            while True:
                msg = self.q.get_nowait()
                if msg[0] == "ai":
                    self._on_ai(*msg[1:])
                elif msg[0] == "ai_fail":
                    self.busy = False
                    self.btn_ai.configure(state="normal")
                    self.lbl_state.configure(text="✖ เชื่อมต่อ AI ไม่ได้")
                    messagebox.showerror("AI", "เชื่อมต่อ AI ไม่ได้: %s\nตรวจ API Key และอินเทอร์เน็ตในแท็บ ⚙ ตั้งค่า" % msg[1], parent=self)
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(100, self._poll)

    def _on_ai(self, analysis, comp, note, was_retry, skipped):
        extra = [("warn", "⚠ " + note)] if note else []
        extra += [("warn", "⚠ ส่งรูปนี้ไม่ได้: " + s) for s in skipped]
        if analysis:
            self.analysis = analysis
        if not comp:
            self.busy = False
            self.btn_ai.configure(state="normal")
            self.lbl_state.configure(text="AI อธิบายแล้ว แต่ไม่ได้ส่งข้อมูลสำหรับกรอกฟอร์ม")
            self._show_analysis(analysis or "(AI ไม่ได้ตอบ)", extra + [("err", "\n✖ AI ไม่ได้ส่งข้อมูลอุปกรณ์ในรูปแบบ JSON ลองกดวิเคราะห์อีกครั้ง หรือกรอกฟอร์มเอง")])
            return
        if not self.editing and comp.get("id") in self.app.kb.comp_by_id:
            extra.append(("warn", "⚠ รหัส %s มีในคลังแล้ว ถ้าบันทึกจะถามก่อนเขียนทับ" % comp["id"]))
        self.fill(comp)
        built, err = self.build()
        errs = [err] if err else self._trial(built)[1]
        if errs and not was_retry:
            self._show_analysis(analysis, extra + [("warn", "\n⏳ ข้อมูลรอบแรกยังสร้างโค้ดไม่ผ่าน กำลังให้ AI แก้:"),
                                                   *[("err", "✖ " + e) for e in errs]])
            text, images = self._last
            self._start_ai(text, images, json.dumps(comp, ensure_ascii=False, indent=1), errs)
            return
        self.busy = False
        self.btn_ai.configure(state="normal")
        if errs:
            self.lbl_state.configure(text="กรอกฟอร์มแล้ว แต่ยังมีจุดต้องแก้ (ดูสีแดง)")
            extra += [("err", "\n✖ ยังสร้างโค้ดไม่ผ่าน แก้ในฟอร์มด้านล่างแล้วกด ทดลองสร้างโค้ด:")] + [("err", "  • " + e) for e in errs]
        else:
            self.lbl_state.configure(text="✔ AI กรอกฟอร์มให้แล้ว และทดลองสร้างโค้ดผ่าน")
            extra += [("ok", "\n✔ กรอกฟอร์มแล้ว ทดลองสร้างโค้ดผ่าน ตรวจข้อมูลอีกครั้งแล้วกด บันทึก ได้เลย")]
        self._show_analysis(analysis, extra)

    def offline(self):
        text = self.txt_src.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("วิเคราะห์", "วางโค้ดตัวอย่าง Arduino / MicroPython หรือข้อความเกี่ยวกับอุปกรณ์ก่อน\n"
                                "(แบบไม่ใช้ AI อ่านรูปไม่ได้)", parent=self)
            return
        comp, report = offline_analyze(text, self.app.kb)
        extra = []
        if comp["type"] != "info":
            self.fill(comp)
            built, err = self.build()
            errs = [err] if err else self._trial(built)[1]
            extra = [("err", "✖ " + e) for e in errs] if errs else [("ok", "✔ ทดลองสร้างโค้ดผ่าน")]
        self.analysis = ""
        self._show_analysis("# ผลการวิเคราะห์แบบไม่ใช้ AI\n" + report, extra)
        self.lbl_state.configure(text="วิเคราะห์แบบไม่ใช้ AI แล้ว")

    # ================================================================ ส่วนที่ 2: ฟอร์ม
    def _build_form(self, frm):
        app = self.app
        ttk.Label(frm, text="② ข้อมูลอุปกรณ์" + ("" if self.editing else "  (ข้อความในช่องเป็นตัวอย่างเซนเซอร์ BH1750 แก้ได้เลย หรือให้ AI กรอกให้)"),
                  font=app.fb).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self.v = {}
        r = 2
        for k, label, ex in self.FIELDS:
            ttk.Label(frm, text=label).grid(row=r, column=0, sticky="w", pady=3)
            e = ttk.Entry(frm, width=52, font=app.f)
            if not self.editing:
                e.insert(0, ex)
            e.grid(row=r, column=1, sticky="w", padx=8)
            self.v[k] = e
            r += 1
        ttk.Label(frm, text="ชนิด").grid(row=r, column=0, sticky="w", pady=3)
        self.cmb_type = ttk.Combobox(frm, state="readonly", width=40, values=self.TYPES)
        self.cmb_type.current(0)
        self.cmb_type.grid(row=r, column=1, sticky="w", padx=8)
        r += 1
        for k, label, ex in self.CODE:
            ttk.Label(frm, text=label, wraplength=900, justify="left").grid(row=r, column=0, columnspan=2, sticky="w", pady=(10, 2))
            t = tk.Text(frm, height=8 if k == "helpers" else 4, width=100, font=app.fmono, undo=True)
            if not self.editing:
                t.insert("1.0", ex)
            t.grid(row=r + 1, column=0, columnspan=2, sticky="w")
            self.v[k] = t
            r += 2
        row = ttk.Frame(frm)
        row.grid(row=r, column=0, columnspan=2, sticky="w", pady=12)
        ttk.Button(row, text="🧪 ทดลองสร้างโค้ด", command=self.preview).pack(side="left")
        ttk.Button(row, text="💾 บันทึกลงคลังความรู้", style="Accent.TButton", command=self.save).pack(side="left", padx=8)
        ttk.Button(row, text="ยกเลิก", command=self.destroy).pack(side="left")

    def _set(self, k, value):
        w = self.v[k]
        if isinstance(w, tk.Text):
            w.delete("1.0", "end")
            w.insert("1.0", value)
        else:
            w.delete(0, "end")
            w.insert(0, value)

    def _get(self, k):
        w = self.v[k]
        return (w.get("1.0", "end") if isinstance(w, tk.Text) else w.get()).strip()

    def fill(self, comp):
        """ใส่ข้อมูลอุปกรณ์ลงฟอร์ม (ใช้ทั้งตอนแก้ไข และตอนรับผลจาก AI)"""
        def lst(x):
            return x if isinstance(x, list) else ([x] if x else [])
        self._set("id", str(comp.get("id", "")))
        for k in ("name_th", "name_en", "category", "voltage", "library", "explain_th"):
            self._set(k, str(comp.get(k) or ""))
        self._set("keywords", ", ".join(map(str, lst(comp.get("keywords")))))
        self._set("keys", ", ".join(map(str, lst(comp.get("keys")))))
        sim = comp.get("sim")
        self._set("sim", ", ".join(str(x) for x in sim) if isinstance(sim, list) else "")
        addrs = []
        for a in lst(comp.get("i2c_addr")):
            try:
                addrs.append("0x%02X" % (int(a, 0) if isinstance(a, str) else int(a)))
            except (TypeError, ValueError):
                pass
        self._set("i2c_addr", ", ".join(addrs))
        t = str(comp.get("type", "sensor")).split()[0]
        self.cmb_type.current({"sensor": 0, "actuator": 1, "info": 2}.get(t, 0))
        lines = []
        for p in lst(comp.get("pins")):
            if isinstance(p, str):
                lines.append(p)
                continue
            kind = p.get("kind", "signal")
            label = str(p.get("label", "")).replace("=", "-")
            if kind == "signal":
                s = "%s=signal:%s" % (label, p.get("need") or "out")
                role = p.get("role")
                if role and role != _derived_role(label):
                    s += "@" + role
                lines.append(s)
            else:
                lines.append("%s=%s" % (label, kind))
        self._set("pins", "\n".join(lines))
        self._set("imports", "\n".join(lst(comp.get("imports"))))
        for k in ("setup", "helpers", "read", "on", "off"):
            self._set(k, str(comp.get(k) or ""))
        self._set("warnings", "\n".join(map(str, lst(comp.get("warnings")))))

    def build(self, strict=True):
        """อ่านฟอร์มเป็นข้อมูลอุปกรณ์ คืนค่า (comp, error)"""
        cid = re.sub(r"\W", "_", self._get("id").lower()).strip("_")
        if not cid:
            return None, "ใส่รหัสอุปกรณ์ก่อน"
        if not re.fullmatch(r"[a-z0-9_]+", cid):
            return None, "รหัสอุปกรณ์ต้องเป็นภาษาอังกฤษ ตัวเลข หรือ _ เท่านั้น"
        pins = []
        for line in self._get("pins").splitlines():
            if not line.strip():
                continue
            if "=" not in line:
                return None, "บรรทัดขาไม่ถูกรูปแบบ (ต้องเป็น ชื่อขา=ชนิด): " + line
            label, kind = [x.strip() for x in line.rsplit("=", 1)]
            kind, _, role = kind.partition("@")
            need = None
            if kind.startswith("signal"):
                kind, _, need = kind.partition(":")
                need = need.strip() or "out"
                if need not in NEEDS:
                    return None, "ชนิดสัญญาณไม่ถูกต้อง: " + line
            if kind not in KINDS:
                return None, "ชนิดขาไม่ถูกต้อง: " + line
            role = (re.sub(r"\W", "_", role.strip().upper()) if role.strip() else _derived_role(label)) if kind == "signal" else label
            pins.append(dict(label=label, kind=kind, need=need, role=role))
        sig_roles = [p["role"] for p in pins if p["kind"] == "signal"]
        if not sig_roles:
            return None, "ต้องมีขาสัญญาณอย่างน้อย 1 ขา"
        if len(set(sig_roles)) != len(sig_roles):
            return None, "ชื่อขาสัญญาณซ้ำกัน: " + ", ".join(sig_roles) + " (ใช้ @ชื่อ ตั้งชื่อไม่ให้ซ้ำ)"
        ctype = self.cmb_type.get().split()[0]
        keywords = [k.strip().lower() for k in self._get("keywords").split(",") if k.strip()]
        if not keywords:
            return None, "ใส่คำที่นักเรียนอาจพิมพ์อย่างน้อย 1 คำ"
        comp = dict(id=cid, name_th=self._get("name_th") or cid, name_en=self._get("name_en") or cid, category=self._get("category"),
                    type=ctype, keywords=keywords, voltage=self._get("voltage"), pins=pins,
                    explain_th=self._get("explain_th"), image="images/%s.png" % cid,
                    warnings=[w.strip() for w in self._get("warnings").splitlines() if w.strip()])
        if self.editing and self.editing.get("id") == cid:
            for k in ("image", "gallery", "notes_th", "ai_analysis_th", "bool", "min_interval"):
                if k in self.editing:
                    comp[k] = self.editing[k]
        imports = [l.strip() for l in self._get("imports").splitlines() if l.strip()]
        if imports:
            comp["imports"] = imports
        for k in ("setup", "helpers", "read", "on", "off"):
            if self._get(k):
                comp[k] = self._get(k)
        if self._get("library"):
            comp["library"] = self._get("library")
        addrs = []
        for a in re.split(r"[,\s]+", self._get("i2c_addr")):
            if a:
                try:
                    addrs.append(int(a, 0))
                except ValueError:
                    return None, "ที่อยู่ I2C ไม่ถูกต้อง: %s (ใช้รูปแบบ 0x23)" % a
        if addrs:
            comp["i2c_addr"] = addrs
        if not strict:
            return comp, None
        # ตรวจว่าโค้ดใช้ชื่อขาที่มีอยู่จริง
        code = "\n".join(comp.get(k, "") for k in ("setup", "read", "on", "off"))
        for tok in set(re.findall(r"\{([A-Z0-9_]+)\}", code)):
            name = tok[len("ADC_SETUP_"):] if tok.startswith("ADC_SETUP_") else tok
            if name not in sig_roles and name != "ANGLE":
                return None, "โค้ดใช้ {%s} แต่ไม่มีขาสัญญาณชื่อ %s (ชื่อขาที่มี: %s)" % (tok, name, ", ".join(sig_roles))
        if re.search(r"\{[A-Z][A-Z0-9_]*\}", comp.get("helpers", "")):
            return None, "ฟังก์ชันช่วย (helpers) ใช้ {ชื่อขา} ไม่ได้ ให้สร้างตัวแปรไว้ในโค้ดตั้งค่าแทน"
        if ctype == "sensor":
            comp["keys"] = [k.strip() for k in self._get("keys").split(",") if k.strip()]
            sim = [s.strip() for s in self._get("sim").split(",") if s.strip()]
            try:
                lo, hi = float(sim[0]), float(sim[1])
                comp["sim"] = [int(lo) if lo.is_integer() else lo, int(hi) if hi.is_integer() else hi,
                               "bool" if len(sim) > 2 and sim[2].lower() == "bool" else "float"]
            except (IndexError, ValueError):
                comp["sim"] = [0, 100, "float"]
            if comp["sim"][2] == "bool":
                comp["bool"] = True
            if not comp.get("read") or not comp["keys"]:
                return None, "เซนเซอร์ต้องมีโค้ดอ่านค่าและชื่อค่าที่อ่านได้"
            if not comp.get("setup"):
                return None, "เซนเซอร์ต้องมีโค้ดตั้งค่า"
            bad = [k for k in comp["keys"] if not re.fullmatch(r"[A-Za-z_]\w*", k)]
            if bad:
                return None, "ชื่อค่าที่อ่านได้ต้องเป็นภาษาอังกฤษ ไม่มีช่องว่าง: " + ", ".join(bad)
            missing = [k for k in comp["keys"] if not re.search(r"\b%s\b" % re.escape(k), comp["read"])]
            if missing:
                return None, "โค้ดอ่านค่าไม่ได้กำหนดตัวแปร: " + ", ".join(missing)
        if ctype == "actuator" and not (comp.get("setup") and comp.get("on") and comp.get("off")):
            return None, "อุปกรณ์สั่งงานต้องมีโค้ดตั้งค่า สั่งเปิด และสั่งปิด"
        return comp, None

    def _trial(self, comp):
        """ทดลองสร้างโค้ดด้วยคลังความรู้ชั่วคราว คืนค่า (result, errors)"""
        board = self.app.board()
        if not board["micropython"] or board["family"] == "microbit":
            board = self.app.kb.board_by_id["esp32-devkit"]
        kb = KnowledgeBase()
        kb.components = [c for c in kb.components if c["id"] not in (comp["id"], (self.editing or {}).get("id"))] + [comp]
        kb.reindex()
        gen = CodeGenerator(kb)
        res = gen.generate(("อ่าน " if comp["type"] == "sensor" else "") + comp["keywords"][0], board["id"])
        errs = list(res.errors)
        if comp["id"] not in [c["id"] for c in res.components]:
            errs.append("คำค้นแรก \"%s\" ไปตรงกับอุปกรณ์อื่น ให้ใช้คำที่เฉพาะเจาะจงกว่านี้" % comp["keywords"][0])
        elif len(res.components) > 1:
            others = ", ".join(c["name_en"] for c in res.components if c["id"] != comp["id"])
            errs.append("คำค้นแรก \"%s\" ทำให้โปรแกรมเลือกอุปกรณ์อื่นด้วย (%s) ให้ใช้คำที่เฉพาะเจาะจงกว่านี้" % (comp["keywords"][0], others))
        if comp["type"] != "info":
            errs += check_code(res.code, board)[0]
            if comp["id"] in res.assigned:
                try:
                    compile(gen.test_code(comp, res.assigned[comp["id"]], board), "test", "exec")
                except SyntaxError as e:
                    errs.append("โค้ดตรวจการต่อสายผิดไวยากรณ์: %s" % e.msg)
        return res, errs

    def preview(self):
        comp, err = self.build()
        if err:
            messagebox.showerror("ทดลองสร้างโค้ด", err, parent=self)
            return
        res, errs = self._trial(comp)
        win = tk.Toplevel(self)
        win.title("ตัวอย่างโค้ดที่จะได้")
        t = tk.Text(win, font=self.app.fmono, width=96, height=34)
        t.pack(fill="both", expand=True)
        wiring = "\n".join("#   %s ขา %s -> %s" % (w["comp_name"], w["comp_pin"], w["board_pin"]) for w in res.wiring)
        t.insert("1.0", ("✖ " + "\n✖ ".join(errs) + "\n\n" if errs else "✔ สร้างโค้ดได้\n\n") +
                 "# การต่อสาย:\n" + wiring + "\n\n" + res.code)

    # ---------- บันทึก
    def _save_images(self, cid):
        """บันทึกรูปที่แนบเป็น images/<id>.png, images/<id>_2.png ... คืนค่า (รูปหลัก, รูปเพิ่มเติม)"""
        if not self.attach:
            return None, []
        os.makedirs(IMAGES, exist_ok=True)
        loaded = []
        try:
            from PIL import Image, ImageOps
            for p in self.attach[:6]:
                try:
                    im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
                    im.thumbnail((640, 640))
                    loaded.append(im)
                except Exception:  # noqa: BLE001
                    continue
            names = []
            for i, im in enumerate(loaded):
                stem = cid if i == 0 else "%s_%d" % (cid, i + 1)
                im.save(os.path.join(IMAGES, stem + ".png"))
                names.append("images/%s.png" % stem)
        except ImportError:
            import shutil
            names = []
            for i, p in enumerate([p for p in self.attach[:6] if p.lower().endswith((".png", ".gif"))]):
                stem = cid if i == 0 else "%s_%d" % (cid, i + 1)
                dst = os.path.join(IMAGES, stem + os.path.splitext(p)[1].lower())
                if os.path.abspath(p) != os.path.abspath(dst):
                    shutil.copy(p, dst)
                names.append("images/" + os.path.basename(dst))
        if names:
            for ext in (".jpg", ".jpeg", ".webp", ".JPG", ".JPEG"):   # ลบรูปหลักเก่าที่ชื่อเดียวกัน
                old = os.path.join(IMAGES, cid + ext)
                if os.path.exists(old):
                    os.remove(old)
        return (names[0] if names else None), names[1:]

    def save(self):
        comp, err = self.build()
        if err:
            messagebox.showerror("บันทึกอุปกรณ์", err, parent=self)
            return
        replacing = comp["id"] in self.app.kb.comp_by_id and not (self.editing and self.editing["id"] == comp["id"])
        if replacing and not messagebox.askyesno("บันทึกอุปกรณ์", "มีอุปกรณ์รหัส %s อยู่แล้ว ต้องการแทนที่หรือไม่" % comp["id"], parent=self):
            return
        _, errs = self._trial(comp)
        if errs:
            messagebox.showerror("บันทึกอุปกรณ์", "ยังบันทึกไม่ได้ เพราะโค้ดที่ได้มีปัญหา:\n" + "\n".join(errs), parent=self)
            return
        main, gallery = self._save_images(comp["id"])
        if main:
            comp["image"] = main
            comp["gallery"] = gallery
        elif not self.attach:
            comp.pop("gallery", None)
        notes = self.txt_src.get("1.0", "end").strip()
        if notes:
            comp["notes_th"] = notes[:6000]
        else:
            comp.pop("notes_th", None)
        if self.analysis:
            comp["ai_analysis_th"] = self.analysis[:6000]
        if self.editing and self.editing["id"] != comp["id"]:
            self.app.kb.delete_component(self.editing["id"])
        self.app.kb.save_component(comp)
        self.app.reload_kb(select=comp["id"])
        messagebox.showinfo("บันทึกอุปกรณ์", "บันทึก %s ลงคลังความรู้แล้ว\nพิมพ์คำสั่งที่มีคำว่า \"%s\" ได้เลย" %
                            (comp["name_th"], comp["keywords"][0]), parent=self)
        self.destroy()

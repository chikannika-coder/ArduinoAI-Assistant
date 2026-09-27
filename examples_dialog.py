# -*- coding: utf-8 -*-
"""หน้าต่าง "ตัวอย่าง Arduino" — เลือกตัวอย่างจาก Arduino IDE เปิดเป็นโค้ด C++ ต้นฉบับ หรือโค้ด MicroPython ที่แปลงแล้ว"""
import os
import tkinter as tk
from tkinter import ttk

import examples_lib



class ExamplesDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("📚 ตัวอย่าง Arduino → MicroPython")
        self.geometry("1100x700")
        self.transient(app.root)
        self.examples = examples_lib.load_index()
        self.by_id = {e["id"]: e for e in self.examples}

        top = ttk.Frame(self, padding=(10, 8))
        top.pack(fill="x")
        ttk.Label(top, text="ค้นหา:").pack(side="left")
        self.ent = ttk.Entry(top, width=30, font=app.f)
        self.ent.pack(side="left", padx=6)
        self.ent.bind("<KeyRelease>", lambda e: self._fill())
        self.var_py = tk.BooleanVar(value=bool(app.board()["micropython"]))
        ttk.Checkbutton(top, text="เฉพาะที่มีโค้ด MicroPython (🐍)", variable=self.var_py,
                        command=self._fill).pack(side="left", padx=12)
        ttk.Label(top, text="บอร์ดที่เลือก: " + app.board()["name"], foreground="#5A6478").pack(side="right")

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        left = ttk.Frame(body)
        self.tree = ttk.Treeview(left, show="tree", selectmode="browse")
        sb = ttk.Scrollbar(left, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._show())
        self.tree.bind("<Double-1>", lambda e: self._open_best())
        right = ttk.Frame(body, padding=(10, 0, 0, 0))
        body.add(left, weight=2)
        body.add(right, weight=3)

        self.lbl_title = ttk.Label(right, text="เลือกตัวอย่างทางซ้าย", font=app.fbig)
        self.lbl_title.pack(anchor="w")
        btns = ttk.Frame(right)
        btns.pack(fill="x", pady=6)
        self.btn_py = ttk.Button(btns, text="🐍 เปิดโค้ด MicroPython", style="Accent.TButton",
                                 command=lambda: self._open("py"), state="disabled")
        self.btn_py.pack(side="left")
        self.btn_ino = ttk.Button(btns, text="📄 เปิดโค้ด C++ ต้นฉบับ", command=lambda: self._open("ino"), state="disabled")
        self.btn_ino.pack(side="left", padx=6)
        fr, self.txt = app._text(right)
        fr.pack(fill="both", expand=True)
        self.txt.tag_configure("h", font=app.fb, foreground="#2457C5")
        self.txt.tag_configure("warn", foreground="#D9661A")
        self.txt.tag_configure("code", font=app.fmono, foreground="#1D2433", background="#F1F4F9")
        self.txt.tag_configure("muted", foreground="#5A6478")
        self._fill()

    def _fill(self):
        q = self.ent.get().strip().lower()
        only_py = self.var_py.get()
        self.tree.delete(*self.tree.get_children())
        cats = {}
        for e in self.examples:
            if only_py and "py" not in e:
                continue
            hay = " ".join([e["name"], e["title_th"], e["desc_th"], e["category_th"]]).lower()
            if q and q not in hay:
                continue
            if e["category"] not in cats:
                cats[e["category"]] = self.tree.insert("", "end", text="%s  %s" % (e["category"][:2], e["category_th"]), open=bool(q) or only_py)
            label = "%s%s  (%s) · %s" % ("🐍 " if "py" in e else "     ", e["title_th"], e["name"], e["level"])
            self.tree.insert(cats[e["category"]], "end", iid=e["id"], text=label)

    def _current(self):
        sel = self.tree.selection()
        return self.by_id.get(sel[0]) if sel else None

    def _show(self):
        e = self._current()
        t = self.txt
        t.delete("1.0", "end")
        if not e:
            return
        board = self.app.board()
        self.lbl_title.configure(text="%s  (%s)" % (e["title_th"], e["name"]))
        can_py = "py" in e and board["micropython"]
        self.btn_py.configure(state="normal" if can_py else "disabled")
        self.btn_ino.configure(state="normal")
        t.insert("end", "ระดับ: %s   |   หมวด: %s\n" % (e["level"], e["category_th"]), "muted")
        if e.get("desc_th"):
            t.insert("end", e["desc_th"] + "\n")
        if e.get("boards_th"):
            t.insert("end", "⚠ ใช้ได้กับ: %s\n" % e["boards_th"], "warn")
        if e.get("note_th"):
            t.insert("end", "หมายเหตุ: %s\n" % e["note_th"], "muted")
        if "py" in e:
            if board["micropython"]:
                t.insert("end", "\n🐍 มีโค้ด MicroPython ให้แล้ว โปรแกรมจะเลือกขาให้ตรงกับบอร์ด %s และวาดภาพการต่อสายให้\n" % board["name"])
            else:
                t.insert("end", "\n%s รัน MicroPython ไม่ได้ จึงเปิดได้เฉพาะโค้ด C++ ต้นฉบับ\n" % board["name"], "warn")
        elif board["micropython"]:
            t.insert("end", "\nตัวอย่างนี้ยังไม่มีโค้ด MicroPython ดูตารางคำสั่งด้านล่างเพื่อลองแปลงเอง หรือถาม AI ในแท็บ ④\n", "muted")
        path = os.path.join(examples_lib.FOLDER, e["ino"])
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                ino = f.read()
        except OSError:
            ino = ""
        refs = self.app.kb.ref_for_code(ino)
        if refs:
            t.insert("end", "\nคำสั่ง Arduino ในตัวอย่างนี้ → เขียนใน MicroPython ว่า\n", "h")
            for r in refs:
                t.insert("end", "• %s — %s\n" % (r["name"], r.get("th", "")))
                t.insert("end", "    " + r["micropython"].replace("\n", "\n    ") + "\n", "code")
        t.insert("end", "\nโค้ด C++ ต้นฉบับ\n", "h")
        t.insert("end", ino, "code")

    def _open_best(self):
        e = self._current()
        if e:
            self._open("py" if "py" in e and self.app.board()["micropython"] else "ino")

    def _open(self, kind):
        e = self._current()
        if not e:
            return
        self.app.open_example(e, kind)
        self.destroy()

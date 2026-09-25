# -*- coding: utf-8 -*-
"""แอนิเมชันการต่อวงจร และภาพการทำงานแบบเรียลไทม์

- โหมดต่อสาย: สายค่อย ๆ ลากจากขาบอร์ดไปยังขาอุปกรณ์ทีละเส้น พร้อมคำบรรยาย
- โหมดทำงาน: จุดสัญญาณวิ่งบนสาย แสดงทิศทางของข้อมูล และอุปกรณ์เรืองแสงเมื่อทำงาน
"""
import tkinter as tk

WIRE_COLORS = {"power5": "#E24B4A", "power3": "#EF9F27", "gnd": "#5F5E5A"}
SIGNAL_COLORS = ["#378ADD", "#1D9E75", "#7F77DD", "#D4537E", "#639922", "#185FA5", "#BA7517"]
KIND_TH = {"power5": "ไฟเลี้ยง 5V", "power3": "ไฟเลี้ยง 3.3V", "gnd": "กราวด์ (GND)", "signal": "สายสัญญาณ"}


class WiringCanvas(tk.Canvas):
    BX, BW = 40, 230          # กล่องบอร์ด
    CX, CW = 610, 250         # กล่องอุปกรณ์
    PAD = 34

    def __init__(self, master, font_family="Tahoma", on_caption=None, **kw):
        super().__init__(master, bg="#FFFFFF", highlightthickness=0, **kw)
        self.ff = font_family
        self.on_caption = on_caption or (lambda *a: None)
        self.result = None
        self.board = None
        self.paths = []
        self.lines = []
        self.step = 0
        self._anim = None
        self._live = None
        self.live_on = False
        self.pulses = []
        self.values = {}
        self.states = {}
        self.comp_boxes = {}
        self.onboard_led = None
        self.bind("<Configure>", lambda e: None)

    # ------------------------------------------------------------ วาดฉาก
    def load(self, result, board):
        self.stop_live()
        self._cancel()
        self.delete("all")
        self.result, self.board = result, board
        self.paths, self.lines, self.step = [], [], 0
        self.comp_boxes, self.onboard_led = {}, None
        wiring = result.wiring if result else []
        if not result or not result.components:
            self.create_text(450, 200, text="สร้างโค้ดก่อน แล้วภาพการต่อวงจรจะแสดงที่นี่",
                             font=(self.ff, 16), fill="#5A6478")
            self.on_caption("ยังไม่มีวงจร", 0, 0)
            return

        # ขาบอร์ดที่ใช้ (ไม่ซ้ำ)
        board_pins = []
        for w in wiring:
            if w["board_pin"] not in board_pins:
                board_pins.append(w["board_pin"])
        top = 40
        bh = max(220, len(board_pins) * self.PAD + 110)
        colr = "#1F3B5C" if board["family"] != "avr" else "#0F6E73"
        self.create_rectangle(self.BX, top, self.BX + self.BW, top + bh, fill=colr, outline="#0B1B2E", width=2)
        self.create_text(self.BX + self.BW / 2, top + 22, text=board["name"][:30], fill="#FFFFFF",
                         font=(self.ff, 11, "bold"), width=self.BW - 20)
        self.create_rectangle(self.BX + 30, top + 48, self.BX + 110, top + 98, fill="#2C2C2A", outline="#888780")
        self.create_text(self.BX + 70, top + 73, text="CHIP", fill="#D3D1C7", font=(self.ff, 9))
        self.create_rectangle(self.BX + self.BW / 2 - 18, top + bh - 14, self.BX + self.BW / 2 + 18, top + bh + 6,
                              fill="#B4B2A9", outline="#5F5E5A")
        self.create_text(self.BX + self.BW / 2, top + bh + 18, text="USB", fill="#5F5E5A", font=(self.ff, 9))
        led_pin = board.get("led")
        if led_pin is not None:
            self.onboard_led = self.create_oval(self.BX + 140, top + 58, self.BX + 156, top + 74, fill="#444441", outline="#D3D1C7")
            self.create_text(self.BX + 148, top + 86, text="LED", fill="#D3D1C7", font=(self.ff, 8))
        bpad = {}
        for i, bp in enumerate(board_pins):
            y = top + 120 + i * self.PAD
            x = self.BX + self.BW
            self.create_rectangle(x - 8, y - 7, x + 6, y + 7, fill="#EF9F27", outline="#854F0B")
            self.create_text(x - 14, y, text=bp, anchor="e", fill="#FFFFFF", font=(self.ff, 10))
            bpad[bp] = (x + 6, y)

        # กล่องอุปกรณ์
        cpad = {}
        y = top
        for c in result.components:
            pins = [w for w in wiring if w["comp"] == c["id"]]
            h = 62 + max(1, len(pins)) * 28 + 24
            fill = "#EEF1F6" if c["type"] != "actuator" else "#FCE9DA"
            box = self.create_rectangle(self.CX, y, self.CX + self.CW, y + h, fill=fill, outline="#98A2B5", width=2)
            self.create_text(self.CX + self.CW / 2, y + 16, text=c["name_en"], font=(self.ff, 11, "bold"), fill="#1D2433")
            self.create_text(self.CX + self.CW / 2, y + 36, text=c["name_th"][:28], font=(self.ff, 9), fill="#5A6478")
            for j, w in enumerate(pins):
                py = y + 62 + j * 28
                self.create_rectangle(self.CX - 6, py - 6, self.CX + 8, py + 6, fill="#D3D1C7", outline="#5F5E5A")
                self.create_text(self.CX + 16, py, text=w["comp_pin"], anchor="w", font=(self.ff, 10), fill="#1D2433")
                cpad[(c["id"], w["comp_pin"])] = (self.CX - 6, py)
            val = self.create_text(self.CX + self.CW / 2, y + h - 16, text="", font=(self.ff, 12, "bold"), fill="#0F6E56")
            self.comp_boxes[c["id"]] = dict(box=box, val=val, fill=fill, type=c["type"])
            if not pins:
                self.create_text(self.CX + self.CW / 2, y + 70, text="ไฟบนบอร์ด ไม่ต้องต่อสาย", font=(self.ff, 10), fill="#5A6478")
            y += h + 18
        total_h = max(y, top + bh + 40) + 20
        self.configure(scrollregion=(0, 0, 900, total_h))

        # เส้นทางสาย (โค้ง Bezier)
        sig_i = 0
        for i, w in enumerate(wiring):
            x1, y1 = bpad[w["board_pin"]]
            x2, y2 = cpad[(w["comp"], w["comp_pin"])]
            if w["kind"] == "signal":
                color = SIGNAL_COLORS[sig_i % len(SIGNAL_COLORS)]
                sig_i += 1
            else:
                color = WIRE_COLORS[w["kind"]]
            dx = 70 + (i % 6) * 22
            pts = []
            for k in range(41):
                t = k / 40
                a, b, cc, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
                pts.append((a * x1 + b * (x1 + dx) + cc * (x2 - dx) + d * x2,
                            a * y1 + b * y1 + cc * y2 + d * y2))
            self.paths.append(dict(w=w, pts=pts, color=color))
            self.lines.append(None)
        self._caption()

    # ------------------------------------------------------------ ควบคุมการต่อสาย
    def _caption(self):
        n = len(self.paths)
        if n == 0:
            self.on_caption("ไม่ต้องต่อสาย ใช้อุปกรณ์บนบอร์ดได้เลย", 0, 0)
        elif self.step == 0:
            self.on_caption("กด \"เล่น\" หรือ \"ถัดไป\" เพื่อดูการต่อสายทีละเส้น (%d เส้น)" % n, 0, n)
        else:
            w = self.paths[self.step - 1]["w"]
            self.on_caption("สายที่ %d: ต่อขา %s ของ %s เข้ากับขา %s ของบอร์ด (%s)" %
                            (self.step, w["comp_pin"], w["comp_name"], w["board_pin"], KIND_TH[w["kind"]]), self.step, n)

    def _draw_wire(self, i, upto=41):
        if self.lines[i]:
            self.delete(self.lines[i])
        p = self.paths[i]
        flat = [v for pt in p["pts"][:max(2, upto)] for v in pt]
        self.lines[i] = self.create_line(*flat, fill=p["color"], width=4, smooth=True, capstyle="round")
        self.tag_lower(self.lines[i])

    def _cancel(self):
        if self._anim:
            self.after_cancel(self._anim)
            self._anim = None

    def next_step(self, animate=True, then=None):
        if self.step >= len(self.paths):
            return False
        self._cancel()
        i = self.step
        self.step += 1
        self._caption()
        if not animate:
            self._draw_wire(i)
            return True

        def grow(k=2):
            self._draw_wire(i, k)
            if k < 41:
                self._anim = self.after(18, grow, k + 3)
            else:
                self._anim = None
                if then:
                    then()
        grow()
        return True

    def prev_step(self):
        self._cancel()
        if self.step > 0:
            self.step -= 1
            if self.lines[self.step]:
                self.delete(self.lines[self.step])
                self.lines[self.step] = None
        self._caption()

    def play(self):
        self._cancel()
        if self.step >= len(self.paths):
            self.reset()

        def chain():
            if self.step < len(self.paths):
                self._anim = self.after(500, lambda: self.next_step(True, chain))
        self.next_step(True, chain)

    def focus_current(self):
        """ทำให้สายเส้นล่าสุดหนาขึ้น นักเรียนจะเห็นชัดว่าต้องต่อเส้นไหน"""
        for i, l in enumerate(self.lines):
            if l:
                self.itemconfigure(l, width=9 if i == self.step - 1 else 4)
        if 0 < self.step <= len(self.lines) and self.lines[self.step - 1]:
            self.tag_raise(self.lines[self.step - 1])

    def reset(self):
        self._cancel()
        for i, l in enumerate(self.lines):
            if l:
                self.delete(l)
            self.lines[i] = None
        self.step = 0
        self._caption()

    def show_all(self):
        self._cancel()
        for i in range(len(self.paths)):
            self._draw_wire(i)
        self.step = len(self.paths)
        self._caption()

    # ------------------------------------------------------------ โหมดทำงานเรียลไทม์
    def start_live(self):
        if not self.paths and not self.comp_boxes:
            return
        self.show_all()
        self.live_on = True
        for p in self.pulses:
            self.delete(p["id"])
        self.pulses = []
        for i, p in enumerate(self.paths):
            if p["w"]["kind"] != "signal":
                continue
            ctype = self.comp_boxes.get(p["w"]["comp"], {}).get("type")
            for k in range(2):
                pid = self.create_oval(0, 0, 0, 0, fill="#FFFFFF", outline=p["color"], width=3, state="hidden")
                self.pulses.append(dict(id=pid, path=i, pos=k * 20, rev=ctype == "sensor", comp=p["w"]["comp"]))
        self.on_caption("โหมดทำงาน: จุดวิ่งบนสายคือข้อมูล เซนเซอร์ส่งข้อมูลเข้าบอร์ด บอร์ดส่งคำสั่งไปยังอุปกรณ์", 0, 0)
        self._tick()

    def stop_live(self):
        self.live_on = False
        if self._live:
            self.after_cancel(self._live)
            self._live = None
        for p in self.pulses:
            self.delete(p["id"])
        self.pulses = []

    def set_live(self, values, states):
        self.values.update(values)
        self.states = states
        if not self.result:
            return
        for c in self.result.components:
            box = self.comp_boxes.get(c["id"])
            if not box:
                continue
            if c["type"] == "sensor":
                txt = "   ".join("%s = %s" % (k, _fmt(self.values[k])) for k in c.get("keys", []) if k in self.values)
                self.itemconfigure(box["val"], text=txt)
            elif c["type"] == "actuator":
                on = states.get(c["id"])
                if on is None:
                    continue
                self.itemconfigure(box["box"], fill="#FAC775" if on else box["fill"], outline="#BA7517" if on else "#98A2B5")
                label = {"led": "ติด", "buzzer": "ดัง ♪", "buzzer_passive": "ดัง ♪", "relay": "ทำงาน", "servo": "หมุน",
                         "motor_l298n": "หมุน", "neopixel": "ติด", "stepper": "หมุน"}.get(c["id"], "ทำงาน")
                self.itemconfigure(box["val"], text=label if on else "หยุด", fill="#854F0B" if on else "#5F5E5A")
                if c["id"] == "led" and self.onboard_led and not any(w["comp"] == "led" for w in self.result.wiring):
                    self.itemconfigure(self.onboard_led, fill="#FFD84D" if on else "#444441")

    def _tick(self):
        if not self.live_on:
            return
        for p in self.pulses:
            show = True
            if not p["rev"]:
                show = bool(self.states.get(p["comp"], True))
            pts = self.paths[p["path"]]["pts"]
            p["pos"] = (p["pos"] + 1) % 40
            idx = 40 - p["pos"] if p["rev"] else p["pos"]
            x, y = pts[idx]
            self.coords(p["id"], x - 6, y - 6, x + 6, y + 6)
            self.itemconfigure(p["id"], state="normal" if show else "hidden")
            self.tag_raise(p["id"])
        self._live = self.after(45, self._tick)


def _fmt(v):
    return str(int(v)) if float(v).is_integer() else "%.1f" % v

# -*- coding: utf-8 -*-
"""รูปวาดอุปกรณ์ (เพิ่มในเวอร์ชัน 2.6)

วาดด้วยคำสั่งของ tkinter Canvas ทั้งหมด ไม่ใช้ไฟล์รูป จึงไม่มีปัญหาลิขสิทธิ์และย่อ/ขยายได้
  draw(canvas, comp_id, cx, cy, size, tag)      -> คืน Device ที่สั่งให้ขยับได้
  Device.update(on=..., value=..., t=...)       -> LED สว่าง เซอร์โวหมุนแขน พัดลมหมุน บัซเซอร์มีคลื่นเสียง ฯลฯ

ระบบพิกัด: รูปทุกรูปวาดในกรอบ -50..50 (กว้าง 100) แล้วย่อ/ขยายตาม size
อุปกรณ์ที่ยังไม่มีรูปเฉพาะ จะได้รูปโมดูลเซนเซอร์หรือกล่องทั่วไปพร้อมชื่อ
"""
import math

PCB_BLUE = "#1C5FA8"
PCB_GREEN = "#2E7D32"
PCB_RED = "#B3261E"
PCB_PURPLE = "#5B3E9E"
PCB_BLACK = "#222222"
PIN = "#C9A227"
METAL = "#B8BEC6"
DARK = "#2B2B2B"


class Pen:
    """ตัวช่วยวาด: แปลงพิกัด -50..50 เป็นพิกัดจริงบน Canvas"""

    def __init__(self, c, cx, cy, size, tag):
        self.c, self.cx, self.cy, self.k, self.tag = c, cx, cy, size / 100.0, tag

    def p(self, x, y):
        return self.cx + x * self.k, self.cy + y * self.k

    def _pts(self, pts):
        out = []
        for x, y in pts:
            out += self.p(x, y)
        return out

    def w(self, v):
        return max(1, v * self.k)

    def rect(self, x1, y1, x2, y2, fill="", outline="#333333", width=1, **kw):
        return self.c.create_rectangle(*self.p(x1, y1), *self.p(x2, y2), fill=fill, outline=outline,
                                       width=self.w(width), tags=self.tag, **kw)

    def oval(self, x1, y1, x2, y2, fill="", outline="#333333", width=1, **kw):
        return self.c.create_oval(*self.p(x1, y1), *self.p(x2, y2), fill=fill, outline=outline,
                                  width=self.w(width), tags=self.tag, **kw)

    def circle(self, x, y, r, **kw):
        return self.oval(x - r, y - r, x + r, y + r, **kw)

    def line(self, *pts, fill="#333333", width=1, **kw):
        return self.c.create_line(*self._pts(pts), fill=fill, width=self.w(width), tags=self.tag, **kw)

    def poly(self, *pts, fill="", outline="#333333", width=1, **kw):
        return self.c.create_polygon(*self._pts(pts), fill=fill, outline=outline, width=self.w(width), tags=self.tag, **kw)

    def arc(self, x1, y1, x2, y2, start, extent, outline="#333333", width=1, style="arc", **kw):
        return self.c.create_arc(*self.p(x1, y1), *self.p(x2, y2), start=start, extent=extent, style=style,
                                 outline=outline, width=self.w(width), tags=self.tag, **kw)

    def text(self, x, y, t, size=9, fill="#FFFFFF", bold=False, font="Tahoma", **kw):
        px = max(6, int(round(size * self.k * 1.1)))
        return self.c.create_text(*self.p(x, y), text=t, fill=fill, tags=self.tag,
                                  font=(font, px, "bold") if bold else (font, px), **kw)

    def pins(self, n, y=30, x0=None, gap=8):
        """ขาเฮดเดอร์สีทองที่ขอบล่างของโมดูล"""
        x0 = -(n - 1) * gap / 2 if x0 is None else x0
        for i in range(n):
            x = x0 + i * gap
            self.rect(x - 1.8, y, x + 1.8, y + 9, fill=PIN, outline="#7A5E00", width=0.5)


class Device:
    """ชิ้นส่วนที่ขยับได้ของรูป"""

    def __init__(self, pen, cid):
        self.pen, self.cid, self.parts, self.angle = pen, cid, {}, 0.0

    def update(self, on=None, value=None, t=0):
        c, P = self.pen.c, self.parts
        if "glow" in P:
            c.itemconfigure(P["glow"], state="normal" if on else "hidden")
        if "lens" in P:
            c.itemconfigure(P["lens"], fill=P["lens_on"] if on else P["lens_off"])
        if "ind" in P:
            c.itemconfigure(P["ind"], fill="#FF3B30" if on else "#5A1A1A")
        if "waves" in P:
            for i, wv in enumerate(P["waves"]):
                c.itemconfigure(wv, state="normal" if on and (t + i) % 3 != 0 else "hidden")
        if "arm" in P:                         # เซอร์โว: แขนหมุนไป 90 องศาเมื่อทำงาน
            goal = 90 if on else 0
            self.angle += (goal - self.angle) * 0.35
            px, py, L = P["arm"][1:]
            a = math.radians(-90 + self.angle)
            self.pen.c.coords(P["arm"][0], *self.pen.p(px, py), *self.pen.p(px + L * math.cos(a), py + L * math.sin(a)))
        if "spin" in P:                        # ใบพัด / ล้อ / แกนมอเตอร์หมุน
            if on:
                self.angle = (self.angle + 25) % 360
            cx, cy, r, ids = P["spin"]
            for i, sid in enumerate(ids):
                a = math.radians(self.angle + i * 360 / len(ids))
                self.pen.c.coords(sid, *self.pen.p(cx, cy), *self.pen.p(cx + r * math.cos(a), cy + r * math.sin(a)))
        if "rgb" in P:
            cols = ["#FF3B30", "#34C759", "#0A84FF", "#FFD60A", "#BF5AF2"]
            for i, lid in enumerate(P["rgb"]):
                c.itemconfigure(lid, fill=cols[(i + t) % len(cols)] if on else "#EEEEEE")
        if "cap" in P:                         # ปุ่มกด: หัวปุ่มยุบลงเมื่อกด
            x1, y1, x2, y2 = P["cap"][1]
            dy = 4 if (value or on) else 0
            self.pen.c.coords(P["cap"][0], *self.pen.p(x1, y1 + dy), *self.pen.p(x2, y2 + dy))
        if "screen" in P and value is not None:
            c.itemconfigure(P["screen"], text=str(value)[:14])
        if "fingers" in P:                     # 2.7 มือหุ่นยนต์: นิ้วงอลงทีละนิ้วเมื่อทำงาน
            for i, (fid, x, y, L) in enumerate(P["fingers"]):
                bend = 0.25 if on and (t + i) % 5 < 3 else 1.0
                self.pen.c.coords(fid, *self.pen.p(x, y), *self.pen.p(x, y - L * bend))
        if "bucket" in P:                      # ถังกระดกของเครื่องวัดน้ำฝน
            tilt = 12 if (t % 2 and on) else -12
            x, y, w = P["bucket"][1:]
            dy = w * math.sin(math.radians(tilt))
            self.pen.c.coords(P["bucket"][0], *self.pen.p(x - w, y + dy), *self.pen.p(x + w, y - dy))


# ------------------------------------------------------------------ แม่แบบที่ใช้ซ้ำ
def _module(p, color=PCB_BLUE, label="", npins=3, w=44, h=28, y0=-22):
    p.rect(-w, y0, w, y0 + h * 2, fill=color, outline="#0B1B2E", width=1.5)
    for x in (-w + 6, w - 6):
        p.circle(x, y0 + 6, 3, fill="#DDDDDD", outline="#666666", width=0.5)
    if label:
        p.text(0, y0 + h * 2 - 8, label, size=8)
    p.pins(npins, y=y0 + h * 2)


def _probe(p, d, tip="#111111", body="#1A1A1A", band=None, label=""):
    """หัววัดแบบแท่ง (pH EC DO ความขุ่น) พร้อมสายและบอร์ดขยายสัญญาณ"""
    p.rect(-42, -10, -6, 26, fill=PCB_BLUE, outline="#0B1B2E", width=1.2)
    p.circle(-34, -2, 4, fill=METAL, outline="#555555")
    p.text(-24, 18, label, size=7)
    p.pins(3, y=26, x0=-32)
    p.line((-6, 4), (10, 4), (14, -30), fill=DARK, width=2.5, smooth=True)
    p.rect(8, -44, 22, -30, fill="#333333", outline="#111111")
    p.rect(10, -30, 20, 36, fill=body, outline="#000000")
    if band:
        p.rect(10, 8, 20, 14, fill=band, outline="")
    p.poly((10, 36), (20, 36), (18, 46), (12, 46), fill=tip, outline="#000000")


# ------------------------------------------------------------------ รูปของแต่ละอุปกรณ์
def _led(p, d):
    d.parts["glow"] = p.circle(0, -14, 30, fill="#FFE8A3", outline="", state="hidden")
    p.line((-6, 12), (-6, 46), fill=METAL, width=2.5)       # ขายาว (+)
    p.line((6, 12), (6, 36), fill=METAL, width=2.5)         # ขาสั้น (−)
    p.text(-14, 44, "+", size=11, fill="#C62828", bold=True)
    p.text(14, 34, "−", size=11, fill="#333333", bold=True)
    p.rect(-15, 4, 15, 12, fill="#C62828", outline="#7F1010")
    d.parts["lens"] = p.poly((-13, 5), (-13, -20), (-9, -30), (0, -34), (9, -30), (13, -20), (13, 5),
                             fill="#E53935", outline="#7F1010", width=1.5, smooth=True)
    d.parts["lens_on"], d.parts["lens_off"] = "#FF5A4F", "#C62828"
    p.oval(-7, -26, -2, -14, fill="#FFB3AE", outline="")


def _buzzer(p, d, passive=False):
    if passive:
        p.rect(-32, 10, 32, 34, fill=PCB_GREEN, outline="#123B14", width=1.2)
        p.pins(3, y=34)
    else:
        p.line((-8, 18), (-8, 40), fill=METAL, width=2)
        p.line((8, 18), (8, 34), fill=METAL, width=2)
    p.circle(0, -6, 28, fill="#1B1B1B", outline="#000000", width=1.5)
    p.circle(0, -6, 6, fill="#444444", outline="#000000")
    p.text(-14, -22, "+", size=10, fill="#DDDDDD", bold=True)
    d.parts["waves"] = [p.arc(10 + 8 * i, -30 - 6 * i, 40 + 14 * i, 18 + 6 * i, -40, 80, outline="#0A84FF", width=2.5, state="hidden")
                        for i in range(3)]


def _relay(p, d):
    p.rect(-44, -26, 44, 30, fill=PCB_BLUE, outline="#0B1B2E", width=1.5)
    p.rect(-38, -20, 6, 22, fill="#1F6FEB", outline="#0B3A7E", width=1.2)
    p.text(-16, -8, "RELAY", size=7, bold=True)
    p.text(-16, 6, "5V", size=7)
    for i in range(3):
        p.rect(14, -18 + i * 13, 38, -7 + i * 13, fill="#1B7F3A", outline="#0B3D1B")
        p.circle(26, -12.5 + i * 13, 3.5, fill=METAL, outline="#555555")
    d.parts["ind"] = p.circle(-32, 24, 3, fill="#5A1A1A", outline="")
    p.pins(3, y=30, x0=-12)


def _servo(p, d):
    p.rect(-40, -16, -30, -4, fill="#1565C0", outline="#0B2E66")
    p.rect(30, -16, 40, -4, fill="#1565C0", outline="#0B2E66")
    p.rect(-30, -26, 30, 26, fill="#1976D2", outline="#0B2E66", width=1.5)
    p.text(0, 12, "SG90", size=8, bold=True)
    p.circle(-12, -10, 9, fill="#FFFFFF", outline="#999999")
    d.parts["arm"] = (p.line((-12, -10), (-12, -40), fill="#FFFFFF", width=6, capstyle="round"), -12, -10, 30)
    p.circle(-12, -10, 3, fill="#AAAAAA", outline="")
    for i, col in enumerate(("#8D6E63", "#E53935", "#FB8C00")):
        p.line((20 + i * 3, 26), (20 + i * 3, 44), fill=col, width=2)


def _dc_motor(p, d, driver=True):
    if driver:
        p.rect(-46, 10, -6, 44, fill=PCB_RED, outline="#5E0F0B", width=1.2)
        p.rect(-40, 14, -12, 28, fill="#111111", outline="#000000")
        for i in range(5):
            p.line((-38 + i * 6, 14), (-38 + i * 6, 6), fill="#333333", width=2)
        p.text(-26, 38, "L298N", size=7, bold=True)
    p.rect(-10, -14, 34, 8, fill="#F4C20D", outline="#8A6D00", width=1.2)
    p.rect(-26, -10, -10, 4, fill=METAL, outline="#666666")
    p.circle(36, -3, 20, fill="#222222", outline="#000000", width=1.5)
    p.circle(36, -3, 13, fill="#444444", outline="")
    ids = [p.line((36, -3), (36, -16), fill="#DDDDDD", width=3) for _ in range(3)]
    d.parts["spin"] = (36, -3, 13, ids)


def _stepper(p, d):
    p.rect(-46, 6, -4, 44, fill=PCB_GREEN, outline="#123B14", width=1.2)
    p.rect(-38, 14, -12, 30, fill="#111111", outline="#000000")
    p.text(-25, 38, "ULN2003", size=6)
    p.circle(22, -8, 26, fill=METAL, outline="#555555", width=1.5)
    p.circle(22, -8, 7, fill="#777777", outline="")
    d.parts["spin"] = (22, -8, 18, [p.line((22, -8), (22, -26), fill="#FFD60A", width=3)])
    p.line((0, 8), (-10, 20), fill="#1565C0", width=2)


def _neopixel(p, d):
    p.rect(-48, -10, 48, 10, fill="#111111", outline="#000000")
    d.parts["rgb"] = [p.rect(-42 + i * 22, -6, -30 + i * 22, 6, fill="#EEEEEE", outline="#999999") for i in range(4)]


def _screen(p, d, kind="oled"):
    if kind == "oled":
        p.rect(-40, -30, 40, 30, fill="#1A237E", outline="#0B0F3A", width=1.5)
        p.rect(-34, -20, 34, 18, fill="#050505", outline="#333333")
        d.parts["screen"] = p.text(0, -2, "Hello", size=9, fill="#6EC6FF", font="Consolas")
        p.pins(4, y=-40, gap=7)
    else:
        p.rect(-48, -26, 48, 26, fill=PCB_GREEN, outline="#123B14", width=1.5)
        p.rect(-42, -16, 42, 14, fill="#9ACD32", outline="#556B2F")
        d.parts["screen"] = p.text(0, -2, "LCD 16x2", size=8, fill="#1B3000", font="Consolas")


def _button(p, d):
    p.rect(-22, -6, 22, 20, fill="#2B2B2B", outline="#000000", width=1.2)
    for x in (-16, 16):
        p.line((x, 20), (x, 36), fill=METAL, width=2)
    cap = p.oval(-12, -18, 12, 6, fill="#E53935", outline="#7F1010", width=1.5)
    d.parts["cap"] = (cap, (-12, -18, 12, 6))


def _touch(p, d):
    p.rect(-26, -26, 26, 26, fill="#D98C3A", outline="#7A4A12", width=1.5)
    p.circle(0, 0, 14, fill="#E8A95B", outline="#7A4A12")
    p.line((26, 0), (46, 0), fill=DARK, width=2)
    d.parts["glow"] = p.circle(0, 0, 20, outline="#0A84FF", width=3, state="hidden")


def _pot(p, d):
    p.circle(0, 0, 26, fill="#1E4E8C", outline="#0B1B2E", width=1.5)
    p.circle(0, 0, 14, fill=METAL, outline="#555555")
    d.parts["spin"] = (0, 0, 13, [p.line((0, 0), (0, -13), fill="#222222", width=3)])
    for x in (-10, 0, 10):
        p.line((x, 26), (x, 42), fill=METAL, width=2)


def _hc_sr04(p, d):
    p.rect(-48, -22, 48, 22, fill=PCB_BLUE, outline="#0B1B2E", width=1.5)
    for x in (-24, 24):
        p.circle(x, 0, 17, fill=METAL, outline="#555555", width=1.5)
        p.circle(x, 0, 11, fill="#DADDE2", outline="#888888")
        for r in (3, 6, 9):
            p.circle(x, 0, r, outline="#9AA0A6", width=0.5)
    p.rect(-6, -18, 6, -8, fill="#C0C0C0", outline="#666666")
    p.pins(4, y=22)
    d.parts["waves"] = [p.arc(-60 + 0, -30 - 5 * i, 60, -10 + 5 * i, 60, 60, outline="#34C759", width=2, state="hidden") for i in range(2)]


def _pir(p, d):
    d.parts["glow"] = p.circle(0, -8, 32, fill="#FFE08A", outline="", state="hidden")
    _module(p, PCB_GREEN, "PIR", 3, w=36, h=22, y0=0)
    p.arc(-26, -30, 26, 22, 0, 180, style="chord", outline="#BBBBBB", width=1.5, fill="#F5F5F5")
    for x in (-14, 0, 14):
        p.line((x, -26), (x * 0.7, -4), fill="#DDDDDD", width=1)


def _dht(p, d, white=False):
    body = "#F1F1F1" if white else "#1E88E5"
    p.rect(-24, -38, 24, 26, fill=body, outline="#555555", width=1.5)
    for r in range(6):
        for col in range(4):
            p.rect(-17 + col * 10, -31 + r * 9, -10 + col * 10, -26 + r * 9,
                   fill="#BDBDBD" if white else "#0D47A1", outline="")
    p.text(0, 20, "DHT22" if white else "DHT11", size=7, fill="#333333" if white else "#FFFFFF", bold=True)
    for x in (-12, -4, 4, 12):
        p.line((x, 26), (x, 42), fill=METAL, width=2)


def _ds18b20(p, d):
    p.rect(-6, -44, 6, -6, fill=METAL, outline="#555555", width=1.2)
    p.oval(-6, -48, 6, -40, fill="#D0D4D9", outline="#555555")
    p.line((0, -6), (0, 10), (-20, 30), (-30, 44), fill="#111111", width=4, smooth=True)
    for i, col in enumerate(("#E53935", "#FDD835", "#111111")):
        p.line((-30 + i * 4, 44), (-30 + i * 4, 50), fill=col, width=2)


def _soil(p, d, capacitive=False):
    p.rect(-10, -46, 30, -24, fill=PCB_RED if not capacitive else PCB_BLACK, outline="#333333")
    for x in (-4, 22):
        p.rect(x, -24, x + 8, 44, fill="#D8B24A" if not capacitive else PCB_BLACK, outline="#6D5410", width=1)
    p.pins(3, y=-56, x0=2)
    p.line((10, -56), (-30, -40), fill=DARK, width=2)
    p.rect(-46, -48, -26, -30, fill=PCB_BLUE, outline="#0B1B2E")


def _board_traces(p, d, color=PCB_RED, vertical=False):
    if vertical:
        p.rect(-18, -46, 18, 40, fill=color, outline="#333333", width=1.5)
        for i in range(8):
            p.line((-12, -34 + i * 9), (12, -34 + i * 9), fill="#D0D0D0", width=1.5)
        p.pins(3, y=40)
    else:
        p.rect(-40, -30, 40, 30, fill="#2E3A44", outline="#111111", width=1.5)
        for i in range(6):
            p.line((-32, -22 + i * 9), (32, -22 + i * 9), fill="#C8A23C", width=1.5)


def _mq2(p, d):
    _module(p, PCB_BLUE, "MQ-2", 4, w=34, h=22, y0=4)
    p.circle(0, -12, 20, fill=METAL, outline="#555555", width=1.5)
    for k in range(-16, 17, 6):
        p.line((k, -30), (k, 6), fill="#8A9096", width=0.7)
        p.line((-18, -12 + k), (18, -12 + k), fill="#8A9096", width=0.7)
    d.parts["ind"] = p.circle(26, 12, 3, fill="#5A1A1A", outline="")


def _sensor_led(p, d, top="#1A1A1A", label="", color=PCB_BLUE):
    _module(p, color, label, 3, w=34, h=20, y0=-4)
    p.line((0, -4), (0, -26), fill=METAL, width=2)
    p.oval(-7, -40, 7, -22, fill=top, outline="#000000")
    d.parts["ind"] = p.circle(24, 6, 3, fill="#5A1A1A", outline="")


def _ir_pair(p, d, label="IR"):
    _module(p, PCB_BLUE, label, 3, w=36, h=20, y0=-4)
    for x, col in ((-10, "#E8F4FF"), (10, "#111111")):
        p.line((x, -4), (x, -20), fill=METAL, width=2)
        p.oval(x - 6, -34, x + 6, -18, fill=col, outline="#000000")
    d.parts["ind"] = p.circle(26, 6, 3, fill="#5A1A1A", outline="")


def _tcrt(p, d, label="TCRT5000"):
    _module(p, PCB_BLUE if label != "BEAM" else "#D9A441", label, 3, w=36, h=20, y0=-4)
    p.rect(-14, -26, 14, -8, fill="#111111", outline="#000000")
    p.circle(-6, -17, 5, fill="#1E88E5", outline="")
    p.circle(6, -17, 5, fill="#333333", outline="")
    d.parts["ind"] = p.circle(26, 6, 3, fill="#5A1A1A", outline="")


def _sound(p, d):
    _module(p, PCB_BLUE, "MIC", 4, w=38, h=20, y0=-4)
    p.circle(-18, -18, 12, fill=METAL, outline="#555555", width=1.5)
    p.circle(-18, -18, 7, fill="#222222", outline="")
    p.rect(8, -26, 26, -10, fill="#1E63C4", outline="#0B2E66")
    p.circle(17, -18, 3, fill="#F4C20D", outline="")
    d.parts["waves"] = [p.arc(-50 - 6 * i, -40 - 6 * i, -26 + 6 * i, 4 + 6 * i, 120, 60, outline="#0A84FF", width=2, state="hidden")
                        for i in range(2)]


def _joystick(p, d):
    p.rect(-34, -34, 34, 30, fill=PCB_BLACK, outline="#000000", width=1.5)
    p.circle(0, -4, 22, fill="#444444", outline="#111111")
    p.circle(0, -4, 13, fill="#111111", outline="#000000")
    p.pins(5, y=30, gap=7)


def _chip_board(p, d, color, label, chip="#111111", extra=None):
    p.rect(-30, -28, 30, 24, fill=color, outline="#222222", width=1.5)
    p.rect(-10, -14, 10, 6, fill=chip, outline="#000000")
    p.text(0, 16, label, size=7)
    p.pins(4, y=24, gap=7)
    if extra:
        extra()


def _hx711(p, d):
    p.rect(-48, -30, 30, -12, fill="#C0C4C8", outline="#666666", width=1.5)
    p.circle(-26, -21, 4, fill="#FFFFFF", outline="#777777")
    p.circle(8, -21, 4, fill="#FFFFFF", outline="#777777")
    p.rect(-6, 0, 40, 34, fill=PCB_GREEN, outline="#123B14", width=1.2)
    p.rect(8, 8, 26, 22, fill="#111111", outline="")
    p.text(17, 30, "HX711", size=6)
    for i, col in enumerate(("#E53935", "#111111", "#FFFFFF", "#43A047")):
        p.line((-40 + i * 4, -12), (-6, 4 + i * 5), fill=col, width=1.5)


def _fsr(p, d):
    p.circle(0, -14, 22, fill="#2B2B2B", outline="#000000", width=1.5)
    p.circle(0, -14, 15, fill="#3A3A3A", outline="#555555")
    p.rect(-5, 6, 5, 40, fill="#C9A227", outline="#6D5410")


def _rain_gauge(p, d):
    p.poly((-34, -40), (34, -40), (10, -14), (-10, -14), fill="#222222", outline="#000000", width=1.5)
    p.rect(-30, -14, 30, 38, fill="#3A3A3A", outline="#111111", width=1.2)
    d.parts["bucket"] = (p.line((-18, 14), (18, 14), fill="#F4C20D", width=5), 0, 14, 18)
    p.poly((0, 14), (-4, 24), (4, 24), fill="#888888", outline="")
    d.parts["waves"] = [p.line((-4 + 4 * i, -36 + 10 * i), (-4 + 4 * i, -30 + 10 * i), fill="#4FC3F7", width=2, state="hidden")
                        for i in range(3)]


def _weather_station(p, d):
    p.line((-40, -46), (-40, 46), fill="#9E9E9E", width=5)
    p.poly((-30, -44), (18, -44), (8, -14), (-20, -14), fill="#1A1A1A", outline="#000000")
    for i in range(5):
        p.oval(-26, -10 + i * 9, 14, 0 + i * 9, fill="#F5F5F5", outline="#BDBDBD")
    p.rect(20, -20, 44, 12, fill="#F5F5F5", outline="#9E9E9E")
    p.rect(24, -16, 40, -4, fill="#263238", outline="")


def _mlx(p, d):
    _chip_board(p, d, PCB_BLUE, "MLX90614", chip=METAL)
    p.circle(0, -4, 8, fill=METAL, outline="#555555")
    p.circle(0, -4, 3, fill="#222222", outline="")


def _max30102(p, d):
    _chip_board(p, d, PCB_PURPLE, "MAX30102", chip="#222222")
    d.parts["glow"] = p.circle(0, -4, 6, fill="#FF3B30", outline="", state="hidden")


def _ecg(p, d, label="AD8232"):
    p.rect(-24, -26, 30, 20, fill=PCB_RED, outline="#5E0F0B", width=1.5)
    p.text(3, 12, label, size=7)
    p.line((-20, -6), (-10, -6), (-6, -18), (-2, 8), (2, -6), (24, -6), fill="#FFFFFF", width=1.5)
    for i, col in enumerate(("#E53935", "#FDD835", "#43A047")):
        p.line((-24, -16 + i * 12), (-38, -34 + i * 30), fill=col, width=1.5)
        p.circle(-40, -36 + i * 30, 5, fill="#EEEEEE", outline="#777777")


def _tcs(p, d):
    _chip_board(p, d, PCB_BLUE, "TCS34725")
    d.parts["glow"] = p.circle(-18, -18, 5, fill="#FFFFFF", outline="#AAAAAA")


def _rc522(p, d):
    p.rect(-40, -34, 40, 30, fill=PCB_BLUE, outline="#0B1B2E", width=1.5)
    for i in range(3):
        p.rect(-32 + i * 5, -26 + i * 5, 18 - i * 5, 14 - i * 5, outline="#C8A23C", width=1.2)
    p.rect(22, -10, 34, 2, fill="#111111", outline="")
    p.pins(8, y=30, gap=8)


def _rtc(p, d):
    p.rect(-38, -26, 38, 26, fill=PCB_BLUE, outline="#0B1B2E", width=1.5)
    p.circle(-12, 0, 16, fill=METAL, outline="#555555", width=1.5)
    p.text(-12, 0, "CR2032", size=5, fill="#333333")
    p.rect(12, -10, 30, 8, fill="#111111", outline="")
    p.pins(4, y=26, gap=8)


def _gps(p, d):
    p.rect(-40, -10, 20, 34, fill=PCB_BLUE, outline="#0B1B2E", width=1.5)
    p.rect(-4, -40, 40, 4, fill="#C9A227", outline="#6D5410", width=1.5)
    p.rect(8, -30, 28, -8, fill="#E0E0E0", outline="#9E9E9E")
    d.parts["ind"] = p.circle(-30, 0, 3, fill="#5A1A1A", outline="")


def _transistor(p, d, label="BC337", tab=False):
    if tab:
        p.rect(-18, -44, 18, -10, fill=METAL, outline="#555555")
        p.circle(0, -34, 5, fill="#FFFFFF", outline="#777777")
        p.rect(-18, -12, 18, 18, fill="#111111", outline="#000000")
    else:
        p.arc(-18, -30, 18, 6, 0, 180, style="chord", fill="#111111", outline="#000000")
        p.rect(-18, -12, 18, 18, fill="#111111", outline="#000000")
    p.text(0, 4, label, size=6)
    for x in (-10, 0, 10):
        p.line((x, 18), (x, 44), fill=METAL, width=2)


def _passive(p, d, cid):
    if cid == "diode_1n4001":
        p.line((-48, 0), (-20, 0), fill=METAL, width=2)
        p.line((20, 0), (48, 0), fill=METAL, width=2)
        p.rect(-20, -8, 20, 8, fill="#111111", outline="#000000")
        p.rect(10, -8, 16, 8, fill="#DDDDDD", outline="")
    elif cid == "capacitor_104":
        p.oval(-18, -34, 18, 0, fill="#E0A96D", outline="#8A5A2B", width=1.5)
        p.text(0, -17, "104", size=8, fill="#5A3A1A")
        for x in (-6, 6):
            p.line((x, 0), (x, 40), fill=METAL, width=2)
    elif cid == "resistor":
        p.line((-48, 0), (-24, 0), fill=METAL, width=2)
        p.line((24, 0), (48, 0), fill=METAL, width=2)
        p.oval(-26, -9, 26, 9, fill="#E9D6B0", outline="#8A6D3B", width=1.2)
        for x, col in ((-14, "#8B4513"), (-6, "#111111"), (2, "#E53935"), (14, "#C9A227")):
            p.rect(x - 2, -8, x + 2, 8, fill=col, outline="")
    elif cid == "breadboard":
        p.rect(-48, -30, 48, 30, fill="#F5F5F0", outline="#BDBDBD", width=1.5)
        p.line((-44, -24), (44, -24), fill="#E53935", width=1)
        p.line((-44, 24), (44, 24), fill="#1E88E5", width=1)
        for r in range(4):
            for c in range(12):
                p.rect(-40 + c * 7, -16 + r * 9 + (6 if r > 1 else 0), -38 + c * 7, -14 + r * 9 + (6 if r > 1 else 0),
                       fill="#555555", outline="")
    elif cid == "battery_holder":
        p.rect(-40, -26, 40, 26, fill="#111111", outline="#000000", width=1.5)
        for i in range(3):
            p.rect(-36, -20 + i * 14, 36, -10 + i * 14, fill="#2E7D32" if i != 1 else "#1565C0", outline="#333333")
        p.line((40, -14), (50, -30), fill="#E53935", width=2)
        p.line((40, -8), (50, -24), fill="#111111", width=2)
    elif cid == "tt_motor":
        _dc_motor(p, d, driver=False)
    elif cid == "peristaltic_pump":
        p.rect(-30, -30, 30, 30, fill="#ECEFF1", outline="#78909C", width=1.5)
        p.circle(0, 0, 20, fill="#FFFFFF", outline="#90A4AE")
        d.parts["spin"] = (0, 0, 16, [p.line((0, 0), (0, -16), fill="#546E7A", width=4) for _ in range(3)])
        p.line((-30, 16), (-48, 16), fill="#FFCC80", width=4)
        p.line((30, 16), (48, 16), fill="#FFCC80", width=4)
    elif cid == "lpt_port":
        p.poly((-46, -16), (46, -16), (38, 16), (-38, 16), fill=METAL, outline="#555555", width=1.5)
        for i in range(13):
            p.circle(-36 + i * 6, -6, 1.8, fill="#333333", outline="")
        for i in range(12):
            p.circle(-33 + i * 6, 6, 1.8, fill="#333333", outline="")
        p.text(0, 28, "DB25 (LPT1)", size=8, fill="#333333")
    elif cid == "beam_robot":
        p.rect(-34, -20, 34, 20, fill="#D9A441", outline="#6D5410", width=1.5)
        p.rect(-20, -16, 20, 10, fill="#F5F5F0", outline="#BDBDBD")
        for x in (-44, 34):
            p.rect(x, -24, x + 10, 24, fill="#222222", outline="#000000")
        for x in (-18, 12):
            p.rect(x, 20, x + 8, 30, fill="#166534", outline="")
    else:
        p.rect(-30, -20, 30, 20, fill="#37474F", outline="#111111", width=1.5)
        p.text(0, 0, cid[:10], size=7)


def _beam_motor(p, d):
    _transistor(p, d, "BD679", tab=True)
    d.parts["glow"] = p.circle(34, -30, 8, fill="#FFD60A", outline="", state="hidden")
    p.circle(34, -30, 5, fill="#FFF59D", outline="#C9A227")


def _robot_hand(p, d):
    """มือหุ่นยนต์กระดาษแข็ง 5 นิ้ว + เซอร์โว 5 ตัวที่ฐาน"""
    p.rect(-34, 22, 34, 46, fill="#1976D2", outline="#0B2E66", width=1.2)
    for i in range(5):
        p.rect(-30 + i * 13, 26, -20 + i * 13, 36, fill="#0D47A1", outline="")
    p.poly((-26, 22), (26, 22), (30, -6), (-30, -6), fill="#D7B889", outline="#8A6D3B", width=1.5)
    fingers = []
    for x, L in ((-22, 26), (-9, 34), (4, 38), (17, 32)):
        fingers.append((p.line((x, -6), (x, -6 - L), fill="#C9A26B", width=10, capstyle="round"), x, -6, L))
    thumb = p.line((-30, 8), (-46, -10), fill="#C9A26B", width=10, capstyle="round")
    fingers.insert(0, (thumb, -46, -10, 0))       # นิ้วโป้งวาดเฉียง ไม่ยืด-หด
    d.parts["fingers"] = [f for f in fingers if f[3]]
    for i in range(4):
        p.line((-22 + i * 13, 22), (-22 + i * 13, -2), fill="#555555", width=0.8)   # เอ็นสายเบ็ด
    p.text(0, 41, "SERVO x5", size=6)


def _raspberry_pi5(p, d):
    p.rect(-46, -30, 46, 30, fill=PCB_GREEN, outline="#123B14", width=1.5)
    for i in range(20):
        p.rect(-40 + i * 4, -27, -38 + i * 4, -22, fill=PIN, outline="")
    p.rect(-20, -12, 16, 12, fill=METAL, outline="#555555")
    p.text(-2, 0, "BCM2712", size=5, fill="#333333")
    p.rect(22, -20, 46, -4, fill=METAL, outline="#555555")
    p.rect(22, 2, 46, 18, fill=METAL, outline="#555555")
    p.rect(-40, 16, -24, 30, fill="#DDDDDD", outline="#888888")
    p.text(-24, -14, "Pi 5", size=7, bold=True)
    d.parts["ind"] = p.circle(-40, 8, 3, fill="#5A1A1A", outline="")


def _generic(p, d, comp):
    t = (comp or {}).get("type", "sensor")
    name = ((comp or {}).get("name_en") or "?").split()[0][:10]
    if t == "actuator":
        p.rect(-36, -26, 36, 26, fill="#FFB74D", outline="#8A5A00", width=1.5)
        p.poly((-4, -20), (10, -20), (0, -2), (12, -2), (-8, 22), (-2, 4), (-12, 4), fill="#FFFFFF", outline="")
        d.parts["glow"] = p.circle(28, -18, 6, fill="#FF3B30", outline="", state="hidden")
    else:
        _module(p, PCB_BLUE, "", 3, w=38, h=22, y0=-22)
        p.rect(-14, -12, 14, 6, fill="#111111", outline="")
        p.text(0, 14, name, size=7)
        d.parts["ind"] = p.circle(-28, 14, 3, fill="#5A1A1A", outline="")


DRAW = {
    "led": _led, "buzzer": _buzzer, "buzzer_passive": lambda p, d: _buzzer(p, d, True), "relay": _relay,
    "servo": _servo, "motor_l298n": _dc_motor, "stepper": _stepper, "neopixel": _neopixel,
    "oled": _screen, "lcd1602": lambda p, d: _screen(p, d, "lcd"), "lcd1602_parallel": lambda p, d: _screen(p, d, "lcd"),
    "button": _button, "touch": _touch, "potentiometer": _pot, "joystick": _joystick,
    "ldr": lambda p, d: _sensor_led(p, d, top="#E8A23C", label="LDR"),
    "flame": lambda p, d: _sensor_led(p, d, top="#111111", label="FLAME"),
    "hc_sr04": _hc_sr04, "pir": _pir, "dht11": _dht, "dht22": lambda p, d: _dht(p, d, True), "ds18b20": _ds18b20,
    "soil": _soil, "rain": lambda p, d: _board_traces(p, d), "water_level": lambda p, d: _board_traces(p, d, PCB_RED, True),
    "mq2": _mq2, "ir_obstacle": _ir_pair, "line_tcrt5000": _tcrt, "beam_ir": lambda p, d: _tcrt(p, d, "BEAM"),
    "sound": _sound, "mpu6050": lambda p, d: _chip_board(p, d, PCB_BLUE, "MPU6050"),
    "bmp280": lambda p, d: _chip_board(p, d, PCB_PURPLE, "BMP280", chip=METAL),
    "rc522": _rc522, "fsr402": _fsr, "hx711": _hx711,
    "ph_sensor": lambda p, d: _probe(p, d, label="pH"),
    "ec_sensor": lambda p, d: _probe(p, d, tip=METAL, label="EC"),
    "do_sensor": lambda p, d: _probe(p, d, tip="#FFEB3B", band="#FFEB3B", label="DO"),
    "turbidity": lambda p, d: _probe(p, d, tip="#E3F2FD", body="#EEEEEE", label="NTU"),
    "vl53l0x": lambda p, d: _chip_board(p, d, PCB_PURPLE, "VL53L0X"),
    "sharp_ir": lambda p, d: _ir_pair(p, d, "SHARP"),
    "mlx90614": _mlx, "max30102": _max30102, "ad8232": _ecg, "eeg": lambda p, d: _ecg(p, d, "EEG"),
    "tcs34725": _tcs, "tcs3200": _tcs, "rain_gauge": _rain_gauge, "weather_station": _weather_station,
    "rtc_ds3231": _rtc, "gps_neo6m": _gps, "bc337": lambda p, d: _transistor(p, d, "BC337"),
    "bd679": lambda p, d: _transistor(p, d, "BD679", tab=True), "beam_motor": _beam_motor,
    "robot_hand": _robot_hand, "raspberry_pi5": _raspberry_pi5,
}


def draw(canvas, cid, cx, cy, size, tag="icon", comp=None, font="Tahoma"):
    """วาดรูปอุปกรณ์ cid ที่จุดกึ่งกลาง (cx, cy) ขนาด size พิกเซล คืน Device"""
    cid = (comp or {}).get("icon", cid)       # 2.7.1: อุปกรณ์หลายตัวชนิดเดียวกัน (servo_1, servo_2 ...) ใช้รูปเดียวกัน
    p = Pen(canvas, cx, cy, size, tag)
    d = Device(p, cid)
    fn = DRAW.get(cid)
    try:
        if fn:
            fn(p, d)
        elif cid in ("diode_1n4001", "capacitor_104", "resistor", "breadboard", "battery_holder", "tt_motor",
                     "peristaltic_pump", "lpt_port", "beam_robot"):
            _passive(p, d, cid)
        else:
            _generic(p, d, comp)
    except Exception:            # noqa: BLE001  รูปวาดพลาดต้องไม่ทำให้โปรแกรมล้ม
        canvas.delete(tag)
        p = Pen(canvas, cx, cy, size, tag)
        d = Device(p, cid)
        _generic(p, d, comp)
    return d


def has_drawing(cid):
    return cid in DRAW or cid in ("diode_1n4001", "capacitor_104", "resistor", "breadboard", "battery_holder",
                                  "tt_motor", "peristaltic_pump", "lpt_port", "beam_robot")

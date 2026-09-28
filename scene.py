# -*- coding: utf-8 -*-
"""ภาพการทำงานของโครงงาน (เพิ่มในเวอร์ชัน 2.6)

วาดเป็นแผนภาพ เหตุ → ผล ที่ขยับตามค่าจริงจากบอร์ดหรือค่าจำลอง
  ซ้าย   : สิ่งที่เซนเซอร์วัด (ดินในกระถาง เทอร์โมมิเตอร์ ท้องฟ้า ถังน้ำ ...) + รูปเซนเซอร์ + แถบค่า
  กลาง   : บอร์ด + กล่องเงื่อนไข "ถ้า ... " บอกว่าตอนนี้จริงหรือไม่
  ขวา    : รูปอุปกรณ์ที่สั่งงาน + ผลที่เกิดขึ้น (น้ำพ่น พัดลมหมุน ไฟสว่าง เสียงดัง ...)
ภาพสร้างเองจากผลของตัวสร้างโค้ด (อุปกรณ์ + เงื่อนไข) จึงใช้ได้กับทุกโปรเจกต์และทุกคำสั่งที่พิมพ์
ทุกอย่างมีตัวอักษรกำกับ ไม่มีข้อมูลที่ต้องฟัง
"""
import math
import tkinter as tk

import icons

BG = "#F6F8FC"
PANEL = "#FFFFFF"
INK = "#1D2433"
MUTED = "#5A6478"
ON = "#E8590C"
OK = "#1E8C5A"

KEY_TH = {
    "soil": ("ความชื้นในดิน", "%"), "temp_c": ("อุณหภูมิ", "°C"), "humidity": ("ความชื้นอากาศ", "%"),
    "light": ("แสง", "%"), "distance_cm": ("ระยะ", "ซม."), "distance_mm": ("ระยะ", "มม."), "ir_distance_cm": ("ระยะ", "ซม."),
    "motion": ("การเคลื่อนไหว", ""), "water": ("ระดับน้ำ", "%"), "water_cm": ("ความลึกน้ำ", "ซม."), "rain": ("น้ำฝนบนแผ่น", "%"),
    "rain_mm": ("ปริมาณน้ำฝน", "มม."), "gas": ("แก๊ส/ควัน", "%"), "weight_g": ("น้ำหนัก", "กรัม"), "ph": ("ค่า pH", ""),
    "ec": ("ค่า EC (ปุ๋ย)", ""), "do_mv": ("ออกซิเจนในน้ำ", "mV"), "do_mgl": ("ออกซิเจนในน้ำ", "mg/L"),
    "turbidity": ("ความขุ่น", "%"), "flame": ("เปลวไฟ", ""), "on_line": ("เจอเส้นดำ", ""), "obstacle": ("เจอสิ่งกีดขวาง", ""),
    "reflect": ("แสงสะท้อน", "%"), "sound": ("เสียง", "%"), "pot": ("ปุ่มหมุน", "%"), "button": ("ปุ่มกด", ""),
    "force": ("แรงกด", "%"), "bpm": ("ชีพจร", "ครั้ง/นาที"), "ecg": ("คลื่นหัวใจ", ""), "obj_temp_c": ("อุณหภูมิวัตถุ", "°C"),
    "amb_temp_c": ("อุณหภูมิห้อง", "°C"), "touch": ("การแตะ", ""), "water_level": ("ระดับน้ำ", "%"),
}
OP_TH = {"<": "น้อยกว่า", "<=": "ไม่เกิน", ">": "มากกว่า", ">=": "ตั้งแต่", "==": "เท่ากับ"}
RANGE = {"temp_c": (0, 50), "obj_temp_c": (20, 45), "amb_temp_c": (0, 50), "distance_cm": (0, 100), "distance_mm": (0, 1000),
         "ir_distance_cm": (0, 80), "water_cm": (0, 60), "rain_mm": (0, 50), "weight_g": (0, 1000), "ph": (0, 14),
         "do_mv": (0, 2000), "do_mgl": (0, 10), "bpm": (40, 160)}
WORLD = {
    "soil": "soil", "temp_c": "temp", "obj_temp_c": "temp", "amb_temp_c": "temp", "humidity": "humid", "light": "sky",
    "distance_cm": "distance", "distance_mm": "distance", "ir_distance_cm": "distance", "motion": "person",
    "water": "tank", "water_cm": "tank", "rain": "rain", "rain_mm": "cylinder", "gas": "smoke", "weight_g": "scale",
    "ph": "ph", "ec": "ec", "do_mv": "bubbles", "do_mgl": "bubbles", "turbidity": "murky", "flame": "fire",
    "on_line": "floorb", "reflect": "floor", "obstacle": "wall", "sound": "bars", "bpm": "heart", "ecg": "heart",
    "force": "press", "button": "press", "touch": "press",
}
RELAY_USE = [  # คำในคำสั่ง -> รีเลย์เปิดอะไร
    (("ปั๊ม", "pump", "รดน้ำ", "เติมน้ำ"), "pump", "ปั๊มน้ำ"),
    (("พัดลม", "fan", "ระบายอากาศ"), "fan", "พัดลม"),
    (("พ่นหมอก", "หมอก", "mist"), "mist", "เครื่องพ่นหมอก"),
    (("เครื่องตีน้ำ", "ตีน้ำ", "ออกซิเจน"), "aerator", "เครื่องตีน้ำ"),
    (("ไฟกก", "ฮีตเตอร์", "ทำความร้อน", "heater", "ความร้อน"), "heat", "ไฟกก / ฮีตเตอร์"),
    (("ไฟปลูก", "หลอดไฟ", "เปิดไฟ", "โคมไฟ", "ไฟ"), "lamp", "หลอดไฟ"),
]
ACT_TH = {"led": "หลอด LED", "buzzer": "บัซเซอร์", "buzzer_passive": "บัซเซอร์", "servo": "เซอร์โว", "relay": "รีเลย์",
          "motor_l298n": "มอเตอร์", "beam_motor": "มอเตอร์ล้อ", "stepper": "สเต็ปมอเตอร์", "neopixel": "ไฟ RGB",
          "oled": "จอ OLED", "lcd1602": "จอ LCD"}
ACT_DOING = {"led": "ติดสว่าง", "buzzer": "ส่งเสียงดัง", "buzzer_passive": "ส่งเสียงดัง", "servo": "หมุนแขน",
             "motor_l298n": "หมุน", "beam_motor": "หมุน", "stepper": "หมุน", "neopixel": "ติดหลายสี",
             "pump": "พ่นน้ำ", "fan": "หมุนเป่าลม", "mist": "พ่นหมอก", "aerator": "ตีน้ำให้มีออกซิเจน",
             "heat": "ให้ความร้อน", "lamp": "สว่าง", "switch": "ทำงาน"}


def _lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _fmt(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    return str(int(v)) if v.is_integer() else "%.1f" % v


class SceneCanvas(tk.Canvas):
    ROW = 200
    W = 1120

    def __init__(self, master, font_family="Tahoma", on_caption=None, on_set=None, **kw):
        super().__init__(master, bg=BG, highlightthickness=0, **kw)
        self.on_set = on_set          # ลากแถบค่าเซนเซอร์เพื่อทดลองเอง: on_set(key, value)
        self.ff = font_family
        self.on_caption = on_caption or (lambda *a: None)
        self.result = None
        self.values, self.states = {}, {}
        self.t = 0
        self.running = False          # มีข้อมูลเข้ามา (จำลองหรือบอร์ดจริง)
        self.visible = False
        self._job = None
        self.sensors, self.acts, self.flows = [], [], []

    # ------------------------------------------------------------ วาดฉาก
    def load(self, result, board, command=""):
        self.delete("all")
        self.result, self.board = result, board
        self.command = (command or "").lower()
        self.values, self.states, self.t = {}, {}, 0
        self.sensors, self.acts, self.flows = [], [], []
        comps = result.components if result else []
        sens = [c for c in comps if c["type"] == "sensor"]
        outs = [c for c in comps if c["type"] in ("actuator", "display")]
        if not comps:
            self.create_text(self.W / 2, 200, text=("โค้ดนี้ไม่มีอุปกรณ์ที่วาดภาพการทำงานได้ ดูรายการขาในแท็บ ① สร้างโค้ด"
                                                     if result and result.code else
                                                     "สร้างโค้ดก่อน แล้วภาพการทำงานของโครงงานจะแสดงที่นี่"),
                             font=(self.ff, 16), fill=MUTED)
            self.configure(scrollregion=(0, 0, self.W, 400))
            return
        rows_s = [(c, k) for c in sens for k in (c.get("keys") or [])[:2]] or []
        n = max(len(rows_s), len(outs), 1)
        H = 90 + n * self.ROW
        self.configure(scrollregion=(0, 0, self.W, H + 20))
        self.create_text(170, 30, text="① สิ่งที่เซนเซอร์วัด", font=(self.ff, 14, "bold"), fill=INK)
        self.create_text(560, 30, text="② บอร์ดคิดตามโค้ด", font=(self.ff, 14, "bold"), fill=INK)
        self.create_text(930, 30, text="③ อุปกรณ์ทำงาน", font=(self.ff, 14, "bold"), fill=INK)

        # บอร์ดตรงกลาง
        by = 60 + n * self.ROW / 2
        self.board_xy = (560, by - 30)
        self._round(460, by - 110, 660, by + 30, fill="#1F3B5C", outline="#0B1B2E", width=3)
        self.create_text(560, by - 88, text=(board or {}).get("name", "บอร์ด").split("(")[0].strip()[:22], fill="#FFFFFF", font=(self.ff, 11, "bold"))
        self.create_rectangle(525, by - 70, 595, by - 20, fill="#2C2C2A", outline="#888780", width=2)
        self.create_text(560, by - 45, text="CPU", fill="#D3D1C7", font=(self.ff, 12, "bold"))
        for i in range(6):
            for side in (-1, 1):
                x = 560 + side * 42
                self.create_line(x, by - 66 + i * 8, x + side * 8, by - 66 + i * 8, fill="#B4B2A9", width=2)
        self.brain = self.create_text(560, by + 5, text="", fill="#FFD60A", font=(self.ff, 11, "bold"))
        self.rule_box = self._round(415, by + 45, 705, by + 150, fill="#FFFFFF", outline="#98A2B5", width=2)
        self.rule_txt = self.create_text(560, by + 82, text=self._rule_text(), font=(self.ff, 12, "bold"), fill=INK,
                                         width=270, justify="center")
        self.rule_ok = self.create_text(560, by + 130, text="", font=(self.ff, 13, "bold"), fill=MUTED)

        # เซนเซอร์ (ซ้าย)
        for i, (c, key) in enumerate(rows_s):
            y = 60 + i * self.ROW + self.ROW / 2 + (n - len(rows_s)) * self.ROW / 2
            self._round(15, y - 88, 330, y + 88, fill=PANEL, outline="#D9DFEA", width=2)
            world = _World(self, WORLD.get(key, "gauge"), 90, y - 12, "w%d" % i)
            dev = icons.draw(self, c["id"], 250, y - 25, 80, tag="s%d" % i, comp=c)
            name, unit = KEY_TH.get(key, (key, ""))
            self.create_text(95, y + 52, text=name, font=(self.ff, 11), fill=MUTED)
            val = self.create_text(95, y + 74, text="–", font=(self.ff, 18, "bold"), fill=INK)
            bar_bg = self.create_rectangle(250 - 45, y + 28, 250 + 45, y + 38, fill="#E6E9F0", outline="")
            bar = self.create_rectangle(250 - 45, y + 28, 250 - 45, y + 38, fill="#378ADD", outline="")
            lo, hi = self._range(c, key)
            hit = self.create_rectangle(200, y + 20, 300, y + 46, fill="", outline="", tags=("hit",))
            self.create_text(250, y + 54, text="↔ ลากแถบเพื่อลองเปลี่ยนค่า", font=(self.ff, 8), fill="#98A2B5")
            for ev in ("<Button-1>", "<B1-Motion>"):
                self.tag_bind(hit, ev, lambda e, k=key, a=lo, b=hi, bl=bool(c.get("bool")): self._drag(e, k, a, b, bl))
            self.tag_bind(hit, "<Enter>", lambda e: self.configure(cursor="sb_h_double_arrow"))
            self.tag_bind(hit, "<Leave>", lambda e: self.configure(cursor=""))
            self.sensors.append(dict(comp=c, key=key, world=world, dev=dev, val=val, bar=bar, bx=(205, 295), y=y,
                                     lo=lo, hi=hi, unit=unit, bool=bool(c.get("bool"))))
            self._flow((330, y), (460, by - 45), "#378ADD", "s", i)

        # อุปกรณ์ที่สั่งงาน (ขวา)
        for i, c in enumerate(outs):
            y = 60 + i * self.ROW + self.ROW / 2 + (n - len(outs)) * self.ROW / 2
            self._round(730, y - 88, 1105, y + 88, fill=PANEL, outline="#D9DFEA", width=2)
            dev = icons.draw(self, c["id"], 800, y - 20, 90, tag="a%d" % i, comp=c)
            use, use_th = self._use(c)
            effect = _Effect(self, use, 990, y - 15, "e%d" % i)
            label = self.create_text(918, y + 66, text="", font=(self.ff, 13, "bold"), fill=MUTED, width=360)
            self.acts.append(dict(comp=c, dev=dev, effect=effect, label=label, use=use, name=use_th, y=y))
            self._flow((660, by - 45), (730, y), ON, "a", i)
        if not outs:
            self._round(730, by - 110, 1105, by + 30, fill=PANEL, outline="#D9DFEA", width=2)
            self.create_text(918, by - 40, text="โครงงานนี้ไม่มีอุปกรณ์สั่งงาน\nบอร์ดส่งค่าไปแสดงเป็นตัวเลขและกราฟ\nในแท็บ ③ ข้อมูลเรียลไทม์",
                             font=(self.ff, 12), fill=MUTED, justify="center")
        self.itemconfigure(self.rule_txt, text=self._rule_text())   # ชื่ออุปกรณ์รู้หลังวาดฝั่งขวาแล้ว
        self._idle_caption()
        self._set_rule_state(None)
        self._schedule()

    def _drag(self, e, key, lo, hi, is_bool):
        if not self.on_set:
            return
        x = self.canvasx(e.x)
        n = max(0.0, min(1.0, (x - 205) / 90.0))
        v = (1 if n > 0.5 else 0) if is_bool else round(lo + (hi - lo) * n, 1)
        self.on_set(key, v)

    def _round(self, x1, y1, x2, y2, r=16, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return self.create_polygon(pts, smooth=True, **kw)

    def _flow(self, a, b, color, kind, idx):
        (x1, y1), (x2, y2) = a, b
        line = self.create_line(x1, y1, (x1 + x2) / 2, y1, (x1 + x2) / 2, y2, x2, y2, smooth=True, fill="#C9D1DE", width=4,
                                arrow="last", arrowshape=(14, 16, 6))
        pts = [(x1 + (x2 - x1) * t / 20, y1 + (y2 - y1) * (3 * (t / 20) ** 2 - 2 * (t / 20) ** 3)) for t in range(21)]
        dots = [self.create_oval(0, 0, 0, 0, fill=color, outline="", state="hidden") for _ in range(3)]
        self.flows.append(dict(line=line, pts=pts, dots=dots, color=color, kind=kind, idx=idx))
        self.tag_lower(line)

    def _range(self, c, key):
        if key in RANGE:
            return RANGE[key]
        sim = c.get("sim")
        if c.get("bool"):
            return 0, 1
        if sim and key in ("soil", "humidity", "light", "water", "rain", "gas", "ec", "turbidity", "reflect", "sound", "pot", "force"):
            return 0, 100
        if sim:
            lo, hi = sim[0], sim[1]
            span = (hi - lo) or 1
            return lo - span * 0.3, hi + span * 0.3
        return 0, 100

    def _use(self, c):
        if c.get("icon"):                                   # 2.7.1: servo_1 ... ใช้ชนิดของอุปกรณ์ต้นแบบ
            use, _ = self._use(dict(c, id=c["icon"], icon=None))
            return use, c["name_th"][:24]
        if c["id"] == "relay":
            for words, use, th in RELAY_USE:
                if any(w in self.command for w in words):
                    return use, th
            return "lamp", "อุปกรณ์ที่ต่อกับรีเลย์"
        if c["id"] in ("motor_l298n", "beam_motor", "tt_motor"):
            return "wheel", ACT_TH.get(c["id"], "มอเตอร์")
        if c["id"] in ("buzzer", "buzzer_passive"):
            return "sound", "บัซเซอร์"
        if c["type"] == "display":
            return "screen", ACT_TH.get(c["id"], c["name_th"])
        return {"led": "light", "servo": "arm", "stepper": "wheel", "neopixel": "rgb"}.get(c["id"], "light"), \
            ACT_TH.get(c["id"], c["name_th"][:20])

    def _rule_text(self):
        r = self.result.rule if self.result else None
        if not r:
            if any(c["type"] == "sensor" for c in self.result.components):
                return "อ่านค่าเซนเซอร์ แล้วส่งค่าออกมาแสดงผล"
            return "สั่งอุปกรณ์ทำงานตามโค้ด" + (" เป็นจังหวะ" if self._blink_mode() else "")
        name, unit = KEY_TH.get(r["key"], (r["key"], ""))
        acts = ", ".join(a["name"] for a in self.acts) if self.acts else "อุปกรณ์"
        cond = "มีการเคลื่อนไหว" if r["key"] == "motion" else (
            "ใช่ (1)" if r["op"] == "==" and r["thr"] == 1 and r["key"] not in ("ph",) else "%s %s %s" % (OP_TH.get(r["op"], r["op"]), _fmt(r["thr"]), unit))
        if r["key"] == "motion":
            return "ถ้า%s\n→ ให้ %s ทำงาน" % (cond, acts)
        return "ถ้า %s %s\n→ ให้ %s ทำงาน" % (name, cond, acts)

    def _blink_mode(self):
        return self.result and not self.result.rule and not any(c["type"] == "sensor" for c in self.result.components)

    # ------------------------------------------------------------ รับข้อมูล
    def set_live(self, values, states):
        self.values.update(values or {})
        if states:
            self.states.update(states)
        self.running = True

    def stop(self):
        self.running = False
        self.states = {}
        self._idle_caption()

    def show(self, visible):
        self.visible = visible
        if visible:
            self._idle_caption() if not self.running else None
            self._schedule()

    def _schedule(self):
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(120, self._tick)

    def _idle_caption(self):
        if self.result and self.result.components and self.visible:
            self.on_caption("ภาพการทำงาน: กด \"⚡ ดูการทำงาน (จำลอง)\" หรือรันบนบอร์ดจริง แล้วดูว่าเซนเซอร์วัดอะไร "
                            "บอร์ดตัดสินใจอย่างไร และอุปกรณ์ทำอะไร", 0, 0)

    def _set_rule_state(self, ok):
        if ok is None:
            self.itemconfigure(self.rule_ok, text="(รอข้อมูล)", fill=MUTED)
            self.itemconfigure(self.rule_box, outline="#98A2B5")
        elif ok:
            self.itemconfigure(self.rule_ok, text="✔ ตอนนี้เป็นจริง", fill=OK)
            self.itemconfigure(self.rule_box, outline=OK)
        else:
            self.itemconfigure(self.rule_ok, text="✘ ตอนนี้ไม่จริง", fill="#C0392B")
            self.itemconfigure(self.rule_box, outline="#C0392B")

    # ------------------------------------------------------------ ขยับภาพ
    def _tick(self):
        if self._job:
            self.after_cancel(self._job)
        self._job = None
        if not self.result or not self.result.components:
            return
        self.t += 1
        blink = self._blink_mode()
        rule = self.result.rule
        act_on = {}
        for a in self.acts:
            cid = a["comp"]["id"]
            if not self.running:
                on = False
            elif blink:
                on = (self.t // 6) % 2 == 0
            elif rule:
                on = bool(self.states.get(cid, False))
            else:
                on = a["comp"]["type"] == "display" or bool(self.states.get(cid, True))
            act_on[cid] = on
        # เซนเซอร์
        for s in self.sensors:
            v = self.values.get(s["key"])
            if v is None:
                s["world"].update(None, None, self.t)
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            norm = (fv - s["lo"]) / ((s["hi"] - s["lo"]) or 1)
            s["world"].update(max(0.0, min(1.0, norm)), fv, self.t)
            txt = ("มี" if fv else "ไม่มี") if s["bool"] else "%s %s" % (_fmt(fv), s["unit"])
            self.itemconfigure(s["val"], text=txt)
            x1, x2 = s["bx"]
            self.coords(s["bar"], x1, s["y"] + 28, x1 + (x2 - x1) * max(0.0, min(1.0, norm)), s["y"] + 38)
            s["dev"].update(on=bool(fv) if s["bool"] else (self.t % 4 < 2), value=fv, t=self.t)
        # เงื่อนไข
        ok = None
        if self.running and rule and rule["key"] in self.values:
            ok = any(act_on.values()) if act_on else None
        if rule:
            self._set_rule_state(ok)
        elif self.running:
            self.itemconfigure(self.rule_ok, text="กำลังทำงาน", fill=OK)
        self.itemconfigure(self.brain, text=("คิด" + "." * (self.t % 4)) if self.running else "")
        # อุปกรณ์
        for a in self.acts:
            on = act_on[a["comp"]["id"]]
            screen = None
            if a["use"] == "screen":
                screen = "  ".join("%s:%s" % (k[:5], _fmt(v)) for k, v in list(self.values.items())[:2]) or "Hello"
            a["dev"].update(on=on, value=screen, t=self.t)
            a["effect"].update(on, self.t)
            doing = ACT_DOING.get(a["use"] if a["comp"]["id"] == "relay" else a["comp"]["id"], "ทำงาน")
            self.itemconfigure(a["label"], text="%s: %s" % (a["name"], doing if on else "หยุด"),
                               fill=ON if on else MUTED)
        # จุดข้อมูลวิ่งบนเส้น
        for f in self.flows:
            active = self.running and (f["kind"] == "s" or act_on.get(self.acts[f["idx"]]["comp"]["id"], False))
            self.itemconfigure(f["line"], fill=f["color"] if active else "#C9D1DE")
            for j, d in enumerate(f["dots"]):
                if not active:
                    self.itemconfigure(d, state="hidden")
                    continue
                k = (self.t * 2 + j * 7) % 21
                x, y = f["pts"][k]
                self.coords(d, x - 6, y - 6, x + 6, y + 6)
                self.itemconfigure(d, state="normal")
                self.tag_raise(d)
        if self.running and self.visible:
            self.on_caption(self._sentence(act_on, ok), 0, 0)
        if self._job:                          # กันตัวจับเวลาซ้อนกันหลายชุด
            self.after_cancel(self._job)
            self._job = None
        if self.visible or self.running:
            self._job = self.after(120, self._tick)

    def _sentence(self, act_on, ok):
        parts = []
        for s in self.sensors[:2]:
            v = self.values.get(s["key"])
            if v is not None:
                name, unit = KEY_TH.get(s["key"], (s["key"], ""))
                parts.append("%s = %s %s" % (name, _fmt(v), unit))
        left = "เซนเซอร์วัดได้ " + ", ".join(parts) if parts else "บอร์ดทำงานตามโค้ด"
        if not self.acts:
            return left + " → ส่งค่าไปแสดงเป็นกราฟ"
        on_names = [a["name"] for a in self.acts if act_on.get(a["comp"]["id"])]
        if self.result.rule:
            verdict = "เงื่อนไขเป็นจริง" if ok else "เงื่อนไขไม่จริง"
            return "%s → %s → %s" % (left, verdict, ("%s ทำงาน" % ", ".join(on_names)) if on_names else "อุปกรณ์หยุด")
        return "%s → %s" % (left, ("%s ทำงาน" % ", ".join(on_names)) if on_names else "อุปกรณ์หยุด")


# ------------------------------------------------------------------ ภาพ "สิ่งที่วัด" ข้างเซนเซอร์
class _World:
    def __init__(self, c, kind, x, y, tag):
        self.c, self.kind, self.x, self.y, self.tag = c, kind, x, y, tag
        self.p = icons.Pen(c, x, y, 120, tag)
        self.parts = {}
        getattr(self, "_draw_" + kind, self._draw_gauge)()

    def update(self, norm, raw, t):
        fn = getattr(self, "_upd_" + self.kind, self._upd_gauge)
        fn(0.5 if norm is None else norm, raw, t, norm is None)

    # ดินในกระถาง: ดินแห้งสีอ่อน ใบไม้เหี่ยว / ดินเปียกสีเข้ม ใบตั้ง
    def _draw_soil(self):
        p = self.p
        p.poly((-30, 10), (30, 10), (22, 44), (-22, 44), fill="#C8733A", outline="#7A3E14", width=1.5)
        self.parts["soil"] = p.rect(-28, 4, 28, 12, fill="#8B5A2B", outline="")
        p.line((0, 6), (0, -30), fill="#2E7D32", width=3)
        self.parts["leaves"] = [p.poly((0, -20), (-22, -30), (-8, -12), fill="#43A047", outline="#1B5E20"),
                                p.poly((0, -26), (22, -36), (8, -18), fill="#43A047", outline="#1B5E20")]

    def _upd_soil(self, n, raw, t, idle):
        self.c.itemconfigure(self.parts["soil"], fill=_lerp_color("#D8B27A", "#4E2E12", n))
        droop = (1 - n) * 18
        L, R = self.parts["leaves"]
        self.c.coords(L, *self.p._pts([(0, -20), (-22, -30 + droop * 1.4), (-8, -12 + droop * 0.4)]))
        self.c.coords(R, *self.p._pts([(0, -26), (22, -36 + droop * 1.4), (8, -18 + droop * 0.4)]))
        col = _lerp_color("#C0A33A", "#43A047", n)
        for lf in (L, R):
            self.c.itemconfigure(lf, fill=col)

    def _draw_temp(self):
        p = self.p
        p.rect(-7, -40, 7, 22, fill="#FFFFFF", outline="#777777", width=1.5)
        p.circle(0, 30, 12, fill="#E53935", outline="#777777", width=1.5)
        self.parts["fill"] = p.rect(-4, 0, 4, 22, fill="#E53935", outline="")
        for i in range(6):
            p.line((8, -34 + i * 10), (14, -34 + i * 10), fill="#999999")

    def _upd_temp(self, n, raw, t, idle):
        top = 22 - n * 60
        self.c.coords(self.parts["fill"], *self.p.p(-4, top), *self.p.p(4, 24))
        self.c.itemconfigure(self.parts["fill"], fill=_lerp_color("#1E88E5", "#E53935", n))

    def _draw_humid(self):
        p = self.p
        p.poly((0, -40), (22, 0), (18, 22), (0, 32), (-18, 22), (-22, 0), smooth=True, fill="#E3F2FD", outline="#1565C0", width=2)
        self.parts["fill"] = p.text(0, 6, "", size=12, fill="#0D47A1", bold=True)

    def _upd_humid(self, n, raw, t, idle):
        self.c.itemconfigure(self.parts["fill"], text="" if idle or raw is None else "%d%%" % round(float(raw)))

    def _draw_sky(self):
        p = self.p
        self.parts["sky"] = p.rect(-40, -40, 40, 34, fill="#90CAF9", outline="#BBBBBB")
        self.parts["sun"] = p.circle(0, -6, 16, fill="#FFD60A", outline="#F4A100", width=2)
        self.parts["rays"] = [p.line((22 * math.cos(a), -6 + 22 * math.sin(a)), (30 * math.cos(a), -6 + 30 * math.sin(a)),
                                     fill="#F4A100", width=2) for a in [k * math.pi / 4 for k in range(8)]]

    def _upd_sky(self, n, raw, t, idle):
        self.c.itemconfigure(self.parts["sky"], fill=_lerp_color("#0B1A3A", "#90CAF9", n))
        bright = n > 0.4
        self.c.itemconfigure(self.parts["sun"], fill="#FFD60A" if bright else "#ECEFF1", outline="#F4A100" if bright else "#B0BEC5")
        for r in self.parts["rays"]:
            self.c.itemconfigure(r, state="normal" if bright else "hidden")

    def _draw_distance(self):
        p = self.p
        p.line((-44, 30), (44, 30), fill="#777777", width=2)
        p.rect(-44, 0, -34, 20, fill="#1C5FA8", outline="")
        self.parts["obj"] = p.rect(-10, 4, 8, 30, fill="#FB8C00", outline="#A65C00")
        self.parts["wave"] = p.line((-34, 10), (-10, 10), fill="#34C759", width=2, dash=(4, 3), arrow="last")

    def _upd_distance(self, n, raw, t, idle):
        x = -28 + n * 66
        self.c.coords(self.parts["obj"], *self.p.p(x, 4), *self.p.p(x + 16, 30))
        self.c.coords(self.parts["wave"], *self.p.p(-34, 12), *self.p.p(x - 2, 12))

    def _draw_person(self):
        p = self.p
        p.rect(-34, -40, 34, 42, fill="#FAFAFA", outline="#CFD8DC", width=1.5)          # ห้อง / พื้นที่ที่เฝ้าดู
        self.parts["empty"] = p.text(0, 0, "ไม่มีใคร", size=10, fill="#90A4AE")
        self.parts["person"] = [p.circle(0, -26, 9, fill="#6D4C41", outline=""),
                                p.poly((-12, -14), (12, -14), (8, 20), (-8, 20), fill="#1976D2", outline=""),
                                p.line((-6, 20), (-10, 40), fill="#37474F", width=4), p.line((6, 20), (10, 40), fill="#37474F", width=4)]
        self.parts["lines"] = [p.line((18 + 5 * i, -10 + 8 * i), (26 + 5 * i, -10 + 8 * i), fill="#FB8C00", width=2) for i in range(3)]

    def _upd_person(self, n, raw, t, idle):
        show = (not idle) and n > 0.5
        for it in self.parts["person"]:
            self.c.itemconfigure(it, state="normal" if show else "hidden")
        self.c.itemconfigure(self.parts["empty"], state="hidden" if show else "normal")
        for it in self.parts["lines"]:
            self.c.itemconfigure(it, state="normal" if show and t % 2 else "hidden")

    def _draw_tank(self):
        p = self.p
        p.rect(-28, -36, 28, 36, fill="#FFFFFF", outline="#607D8B", width=2)
        self.parts["water"] = p.rect(-26, 0, 26, 34, fill="#4FC3F7", outline="")

    def _upd_tank(self, n, raw, t, idle):
        top = 34 - n * 68
        self.c.coords(self.parts["water"], *self.p.p(-26, top), *self.p.p(26, 34))

    _draw_cylinder, _upd_cylinder = _draw_tank, _upd_tank

    def _draw_rain(self):
        p = self.p
        for x, y, r in ((-14, -28, 12), (4, -32, 15), (20, -26, 11)):
            p.circle(x, y, r, fill="#B0BEC5", outline="")
        p.rect(-24, -28, 30, -16, fill="#B0BEC5", outline="")
        self.parts["drops"] = [p.line((-20 + i * 9, -8), (-22 + i * 9, 2), fill="#1E88E5", width=2, state="hidden") for i in range(6)]

    def _upd_rain(self, n, raw, t, idle):
        k = int(round(n * 6))
        for i, d in enumerate(self.parts["drops"]):
            yy = -8 + ((t * 6 + i * 13) % 40)
            self.c.coords(d, *self.p.p(-20 + i * 9, yy), *self.p.p(-22 + i * 9, yy + 8))
            self.c.itemconfigure(d, state="normal" if i < k and not idle else "hidden")

    def _draw_smoke(self):
        self.parts["puffs"] = [self.p.circle(-10 + (i % 3) * 12, 10 - i * 10, 9, fill="#9E9E9E", outline="", state="hidden") for i in range(5)]

    def _upd_smoke(self, n, raw, t, idle):
        k = int(round(n * 5))
        for i, pf in enumerate(self.parts["puffs"]):
            self.c.itemconfigure(pf, state="normal" if i < k and not idle else "hidden",
                                 fill=_lerp_color("#E0E0E0", "#424242", n))

    def _draw_scale(self):
        p = self.p
        p.rect(-30, 16, 30, 30, fill="#90A4AE", outline="#546E7A", width=1.5)
        self.parts["box"] = p.rect(-12, -6, 12, 14, fill="#A1887F", outline="#5D4037")
        self.parts["txt"] = p.text(0, 38, "", size=9, fill=INK, bold=True)

    def _upd_scale(self, n, raw, t, idle):
        s = 6 + n * 16
        self.c.coords(self.parts["box"], *self.p.p(-s, 14 - 2 * s), *self.p.p(s, 14))
        self.c.itemconfigure(self.parts["txt"], text="" if idle else "%s g" % _fmt(raw))

    def _draw_beaker(self, dots=False):
        p = self.p
        p.poly((-24, -30), (24, -30), (24, 34), (-24, 34), fill="", outline="#607D8B", width=2)
        self.parts["liq"] = p.rect(-22, -6, 22, 32, fill="#81D4FA", outline="")
        if dots:
            self.parts["dots"] = [p.circle(-16 + (i * 7) % 32, 0 + (i * 11) % 28, 2, fill="#FFFFFF", outline="", state="hidden") for i in range(10)]

    def _draw_ph(self):
        self._draw_beaker()

    def _upd_ph(self, n, raw, t, idle):
        col = _lerp_color("#E53935", "#43A047", n * 2) if n < 0.5 else _lerp_color("#43A047", "#6A1B9A", (n - 0.5) * 2)
        self.c.itemconfigure(self.parts["liq"], fill=col)

    def _draw_ec(self):
        self._draw_beaker(True)

    def _upd_ec(self, n, raw, t, idle):
        k = int(round(n * 10))
        for i, d in enumerate(self.parts["dots"]):
            self.c.itemconfigure(d, state="normal" if i < k and not idle else "hidden", fill="#FFF59D")

    def _draw_bubbles(self):
        self._draw_beaker(True)

    def _upd_bubbles(self, n, raw, t, idle):
        k = int(round(n * 10))
        for i, d in enumerate(self.parts["dots"]):
            yy = 30 - ((t * 3 + i * 9) % 34)
            xx = -16 + (i * 7) % 32
            self.c.coords(d, *self.p.p(xx - 2, yy - 2), *self.p.p(xx + 2, yy + 2))
            self.c.itemconfigure(d, state="normal" if i < k and not idle else "hidden", fill="#FFFFFF")

    def _draw_murky(self):
        self._draw_beaker()

    def _upd_murky(self, n, raw, t, idle):
        self.c.itemconfigure(self.parts["liq"], fill=_lerp_color("#B3E5FC", "#6D4C41", n))

    def _draw_fire(self):
        self.parts["flame"] = self.p.poly((0, -30), (14, 0), (8, 24), (-8, 24), (-14, 0), smooth=True, fill="#FF7043", outline="#E64A19")

    def _upd_fire(self, n, raw, t, idle):
        s = 0.3 + 0.7 * n
        self.c.coords(self.parts["flame"], *self.p._pts([(0, 24 - 54 * s), (14 * s, 24 - 24 * s), (8 * s, 24), (-8 * s, 24), (-14 * s, 24 - 24 * s)]))
        self.c.itemconfigure(self.parts["flame"], state="hidden" if idle or n < 0.05 else "normal")

    def _draw_floor(self):
        p = self.p
        self.parts["floor"] = p.rect(-40, 10, 40, 34, fill="#FFFFFF", outline="#9E9E9E")
        self.parts["line"] = p.rect(-8, 10, 8, 34, fill="#111111", outline="")
        p.rect(-12, -14, 12, -2, fill="#1C5FA8", outline="")
        p.line((0, -2), (0, 10), fill="#E53935", width=2, arrow="last")

    def _upd_floor(self, n, raw, t, idle):          # reflect: ค่าสูง = พื้นขาว ค่าต่ำ = เส้นดำ
        self.c.itemconfigure(self.parts["line"], state="normal" if n < 0.5 and not idle else "hidden")

    _draw_floorb = _draw_floor

    def _upd_floorb(self, n, raw, t, idle):         # on_line: 1 = อยู่บนเส้นดำ
        self.c.itemconfigure(self.parts["line"], state="normal" if n > 0.5 and not idle else "hidden")

    def _draw_wall(self):
        self.parts["wall"] = self.p.rect(10, -30, 26, 34, fill="#8D6E63", outline="#4E342E", state="hidden")
        self.p.rect(-40, -6, -26, 10, fill="#1C5FA8", outline="")

    def _upd_wall(self, n, raw, t, idle):
        self.c.itemconfigure(self.parts["wall"], state="normal" if n > 0.5 and not idle else "hidden")

    def _draw_bars(self):
        self.parts["bars"] = [self.p.rect(-30 + i * 12, 0, -22 + i * 12, 30, fill="#7E57C2", outline="") for i in range(6)]

    def _upd_bars(self, n, raw, t, idle):
        for i, b in enumerate(self.parts["bars"]):
            h = 4 + n * 60 * (0.5 + 0.5 * math.sin(t + i))
            self.c.coords(b, *self.p.p(-30 + i * 12, 30 - h), *self.p.p(-22 + i * 12, 30))

    def _draw_heart(self):
        self.parts["heart"] = self.p.text(0, -14, "♥", size=34, fill="#E53935", bold=True)
        self.parts["wave"] = self.p.line((-40, 24), (40, 24), fill="#E53935", width=2)

    def _upd_heart(self, n, raw, t, idle):
        pts = []
        for i in range(17):
            x = -40 + i * 5
            y = 24 - (18 if (i + t) % 8 == 0 else (-6 if (i + t) % 8 == 1 else 0))
            pts.append((x, y))
        self.c.coords(self.parts["wave"], *self.p._pts(pts))
        self.c.itemconfigure(self.parts["heart"], fill="#E53935" if t % 4 < 2 else "#FF8A80")

    def _draw_press(self):
        self.parts["hand"] = self.p.poly((-8, -40), (8, -40), (8, -10), (-8, -10), fill="#FFCC80", outline="#A1887F")
        self.p.rect(-20, 10, 20, 20, fill="#424242", outline="")

    def _upd_press(self, n, raw, t, idle):
        dy = n * 18
        self.c.coords(self.parts["hand"], *self.p._pts([(-8, -40 + dy), (8, -40 + dy), (8, -10 + dy), (-8, -10 + dy)]))

    def _draw_gauge(self):
        p = self.p
        p.arc(-34, -30, 34, 38, 0, 180, outline="#90A4AE", width=6)
        self.parts["needle"] = p.line((0, 4), (0, -24), fill="#E53935", width=3)

    def _upd_gauge(self, n, raw, t, idle):
        a = math.pi * (1 - n)
        self.c.coords(self.parts["needle"], *self.p.p(0, 4), *self.p.p(28 * math.cos(a), 4 - 28 * math.sin(a)))


# ------------------------------------------------------------------ ผลที่เกิดขึ้นข้างอุปกรณ์
class _Effect:
    def __init__(self, c, use, x, y, tag):
        self.c, self.use, self.tag = c, use, tag
        self.p = icons.Pen(c, x, y, 120, tag)
        self.parts = {}
        self.angle = 0
        getattr(self, "_draw_" + use, self._draw_light)()

    def update(self, on, t):
        getattr(self, "_upd_" + self.use, self._upd_light)(on, t)

    def _draw_light(self):
        p = self.p
        self.parts["rays"] = [p.line((18 * math.cos(a), 18 * math.sin(a)), (32 * math.cos(a), 32 * math.sin(a)), fill="#F4A100", width=3, state="hidden")
                              for a in [k * math.pi / 4 for k in range(8)]]
        self.parts["bulb"] = p.circle(0, 0, 14, fill="#ECEFF1", outline="#9E9E9E", width=2)

    def _upd_light(self, on, t):
        self.c.itemconfigure(self.parts["bulb"], fill="#FFE066" if on else "#ECEFF1")
        for r in self.parts["rays"]:
            self.c.itemconfigure(r, state="normal" if on else "hidden")

    _draw_lamp, _upd_lamp = _draw_light, _upd_light
    _draw_rgb, _upd_rgb = _draw_light, _upd_light

    def _draw_heat(self):
        p = self.p
        p.rect(-20, 14, 20, 24, fill="#5D4037", outline="")
        self.parts["waves"] = [p.line((-12 + i * 12, 8), (-8 + i * 12, -2), (-12 + i * 12, -12), (-8 + i * 12, -22),
                                      smooth=True, fill="#FF7043", width=3, state="hidden") for i in range(3)]

    def _upd_heat(self, on, t):
        for i, w in enumerate(self.parts["waves"]):
            self.c.itemconfigure(w, state="normal" if on and (t + i) % 3 else "hidden")

    def _draw_pump(self):
        p = self.p
        p.line((-44, 0), (0, 0), (0, -18), fill="#607D8B", width=5)
        p.rect(-8, -26, 8, -18, fill="#455A64", outline="")
        self.parts["drops"] = [p.oval(-2, -10, 2, -4, fill="#1E88E5", outline="", state="hidden") for _ in range(8)]
        p.poly((-26, 34), (26, 34), (18, 44), (-18, 44), fill="#C8733A", outline="")
        self.parts["plant"] = p.line((0, 34), (0, 18), fill="#2E7D32", width=3)

    def _upd_pump(self, on, t):
        for i, d in enumerate(self.parts["drops"]):
            k = (t * 2 + i * 3) % 12
            dx = (i % 4 - 1.5) * 5 * (k / 12 + 0.3)
            yy = -18 + k * 4
            self.c.coords(d, *self.p.p(dx - 2, yy - 3), *self.p.p(dx + 2, yy + 3))
            self.c.itemconfigure(d, state="normal" if on else "hidden")

    def _draw_mist(self):
        p = self.p
        p.rect(-40, -4, -24, 8, fill="#90A4AE", outline="")
        self.parts["dots"] = [p.circle(-20 + (i % 6) * 9, -10 + (i // 6) * 9, 2.5, fill="#B3E5FC", outline="", state="hidden") for i in range(18)]

    def _upd_mist(self, on, t):
        for i, d in enumerate(self.parts["dots"]):
            self.c.itemconfigure(d, state="normal" if on and (i + t) % 4 else "hidden")

    def _draw_aerator(self):
        p = self.p
        p.rect(-30, -10, 30, 34, fill="#4FC3F7", outline="#0277BD", width=1.5)
        self.parts["dots"] = [p.circle(-20 + i * 8, 20, 3, fill="#FFFFFF", outline="", state="hidden") for i in range(6)]

    def _upd_aerator(self, on, t):
        for i, d in enumerate(self.parts["dots"]):
            yy = 30 - ((t * 4 + i * 7) % 38)
            xx = -20 + i * 8
            self.c.coords(d, *self.p.p(xx - 3, yy - 3), *self.p.p(xx + 3, yy + 3))
            self.c.itemconfigure(d, state="normal" if on else "hidden")

    def _draw_fan(self):
        p = self.p
        p.circle(0, 0, 32, outline="#90A4AE", width=2)
        self.parts["blades"] = [p.poly((0, 0), (0, 0), (0, 0), fill="#64B5F6", outline="#1E88E5") for _ in range(3)]
        p.circle(0, 0, 5, fill="#455A64", outline="")
        self.parts["wind"] = [p.line((36, -10 + i * 10), (48, -10 + i * 10), fill="#90CAF9", width=2, state="hidden") for i in range(3)]
        self._upd_fan(False, 0)

    def _upd_fan(self, on, t):
        if on:
            self.angle = (self.angle + 35) % 360
        for i, b in enumerate(self.parts["blades"]):
            a = math.radians(self.angle + i * 120)
            pts = [(0, 0), (28 * math.cos(a - 0.35), 28 * math.sin(a - 0.35)), (28 * math.cos(a + 0.35), 28 * math.sin(a + 0.35))]
            self.c.coords(b, *self.p._pts(pts))
        for w in self.parts["wind"]:
            self.c.itemconfigure(w, state="normal" if on and t % 2 else "hidden")

    def _draw_sound(self):
        p = self.p
        self.parts["waves"] = [p.arc(-10 - 10 * i, -18 - 10 * i, 10 + 10 * i, 18 + 10 * i, -50, 100, outline="#0A84FF", width=3, state="hidden") for i in range(3)]
        self.parts["note"] = p.text(-24, -26, "♪", size=20, fill="#0A84FF", bold=True, state="hidden")
        self.parts["txt"] = p.text(0, 38, "สั่น / ดัง", size=9, fill="#0A84FF", bold=True, state="hidden")

    def _upd_sound(self, on, t):
        for i, w in enumerate(self.parts["waves"]):
            self.c.itemconfigure(w, state="normal" if on and (t + i) % 3 else "hidden")
        for k in ("note", "txt"):
            self.c.itemconfigure(self.parts[k], state="normal" if on else "hidden")

    def _draw_arm(self):
        p = self.p
        p.rect(-6, 10, 6, 40, fill="#8D6E63", outline="")
        self.parts["gate"] = p.line((0, 10), (40, 10), fill="#E53935", width=6, capstyle="round")
        self.a = 0

    def _upd_arm(self, on, t):
        goal = 80 if on else 0
        self.a += (goal - self.a) * 0.3
        r = math.radians(self.a)
        self.c.coords(self.parts["gate"], *self.p.p(0, 10), *self.p.p(40 * math.cos(r), 10 - 40 * math.sin(r)))

    def _draw_wheel(self):
        p = self.p
        p.circle(0, 0, 28, fill="#212121", outline="#000000", width=2)
        p.circle(0, 0, 18, fill="#616161", outline="")
        self.parts["spokes"] = [p.line((0, 0), (0, -18), fill="#EEEEEE", width=3) for _ in range(4)]
        self.parts["arrow"] = p.text(0, 40, "", size=9, fill=ON, bold=True)

    def _upd_wheel(self, on, t):
        if on:
            self.angle = (self.angle + 30) % 360
        for i, s in enumerate(self.parts["spokes"]):
            a = math.radians(self.angle + i * 90)
            self.c.coords(s, *self.p.p(0, 0), *self.p.p(18 * math.cos(a), 18 * math.sin(a)))
        self.c.itemconfigure(self.parts["arrow"], text="↻ หมุน" if on else "")

    def _draw_screen(self):
        self.parts["txt"] = self.p.text(0, 0, "แสดงค่า", size=10, fill=MUTED)

    def _upd_screen(self, on, t):
        self.c.itemconfigure(self.parts["txt"], text="แสดงค่าบนจอ" if on else "")

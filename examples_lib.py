# -*- coding: utf-8 -*-
"""คลังตัวอย่าง Arduino (จาก Arduino IDE 1.6.0) พร้อมโค้ด MicroPython ที่แปลงแล้ว

ไฟล์อยู่ในโฟลเดอร์ arduino_examples/
  index.json            รายชื่อตัวอย่าง ชื่อไทย คำอธิบาย ระดับ
  <หมวด>/<ชื่อ>.ino      โค้ด C++ ต้นฉบับ
  <หมวด>/<ชื่อ>.py       โค้ด MicroPython (มีเฉพาะบางตัวอย่าง)

หัวไฟล์ .py บอกโปรแกรมว่าต้องเลือกขาอย่างไร ให้เข้ากับบอร์ดที่นักเรียนเลือก
  # แผนขา: <คำสั่งภาษาไทยที่มีชื่ออุปกรณ์>      -> ให้ตัวสร้างโค้ดเลือกขาและวาดภาพการต่อสาย
  # ขา: led.SIG=LED_PIN, hc_sr04.TRIG=TRIG_PIN   -> ขาของอุปกรณ์ไหนไปใส่ในตัวแปรไหน
  # ขาเพิ่ม: LED_PINS=out*6                       -> ขอขาเพิ่มเป็นรายการ (ไม่มีภาพการต่อสาย)
  # ขาเพิ่ม: RIGHT_SENSOR=adc                      -> ขอขาเพิ่ม 1 ขา ใส่เป็นตัวเลข (2.4)
  # ขาเพิ่ม: S4_PIN=inpu                            -> ขาเข้าที่ใช้ Pin.PULL_UP ไม่เลือกขาที่ไม่มีตัวดึงขึ้น (2.5)
  # ขาเพิ่ม: SERVO_PINS=pwm*5@servo:โป้ง|ชี้|กลาง|นาง|ก้อย
        -> ขอขาเพิ่ม แล้ววาดอุปกรณ์ servo ต่อทีละขาในภาพการต่อสายด้วย ชื่อหลัง : ใช้ต่อท้ายชื่ออุปกรณ์ (2.7.1)
"""
import copy
import json
import os
import re

from generator import Result, board_pin_label, pin_literal, power_label

BASE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.join(BASE, "arduino_examples")


def load_index():
    path = os.path.join(FOLDER, "index.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("examples", [])


def header(code, key):
    m = re.search(r"^#\s*%s:\s*(.+)$" % re.escape(key), code, re.M)
    return m.group(1).strip() if m else ""


def _set_const(code, name, value):
    """แทนค่าบรรทัด NAME = ... (เก็บคอมเมนต์ท้ายบรรทัดไว้)"""
    pat = re.compile(r"^(%s\s*=\s*)([^#\n]*?)(\s*#.*)?$" % re.escape(name), re.M)
    return pat.sub(lambda m: m.group(1) + value + (m.group(3) or ""), code, count=1)


def adapt(code, gen, board):
    """ปรับขาในโค้ด MicroPython ให้ตรงกับบอร์ด คืนค่า (โค้ดใหม่, Result สำหรับภาพการต่อสาย, ข้อความเตือน)"""
    notes = []
    res = Result()
    used = set()
    plan_cmd = header(code, "แผนขา")
    if plan_cmd:
        _, _, res = gen.plan(plan_cmd, board["id"])
        for pair in filter(None, (p.strip() for p in header(code, "ขา").split(","))):
            left, const = (x.strip() for x in pair.split("=", 1))
            cid, role = left.split(".", 1)
            pin = res.assigned.get(cid, {}).get(role)
            if pin is None:
                notes.append("บอร์ดนี้ไม่มีขาว่างสำหรับ %s" % const)
                continue
            code = _set_const(code, const, pin_literal(pin))
        used = {p for roles in res.assigned.values() for p in roles.values()}
        if board.get("i2c"):
            used |= {board["i2c"]["sda"], board["i2c"]["scl"]}
    for pair in filter(None, (p.strip() for p in header(code, "ขาเพิ่ม").split(","))):
        const, spec = (x.strip() for x in pair.split("=", 1))
        spec, _, dev = spec.partition("@")        # 2.7.1: @servo = วาดอุปกรณ์ต่อที่ขาเหล่านี้
        single = "*" not in spec                  # "adc" = ขาเดียว (ตัวเลข), "out*6" = รายการ 6 ขา
        need, n = (spec, "1") if single else spec.split("*")
        pull_up = need == "inpu"                  # 2.5: ขาเข้าที่ใช้ Pin.PULL_UP (ห้ามใช้ขารับอย่างเดียวของ ESP32 ที่ไม่มีตัวดึงขึ้น)
        if pull_up:
            need = "inp"
        pool = [p for p in board["pools"].get(need, []) if p not in used and p not in board.get("serial_pins", [])
                and not (pull_up and p in board.get("input_only", []))]
        pins = pool[:int(n)]
        if len(pins) < int(n):
            notes.append("บอร์ด %s มีขาว่างไม่พอ ต้องการ %s ขา มี %d ขา" % (board["name"], n, len(pins)))
        used.update(pins)
        if single:
            if pins:
                code = _set_const(code, const, pin_literal(pins[0]))
        else:
            code = _set_const(code, const, "[%s]" % ", ".join(pin_literal(p) for p in pins))
        res.explanation.append("%s ต่อที่ขา %s" % (const, ", ".join(board_pin_label(board, p) for p in pins)))
        if dev:
            _add_devices(res, gen, board, dev, pins)
    res.keys = list(dict.fromkeys(re.findall(r"print\(\s*[\"']([A-Za-z_]\w*)\s*:", code)))
    res.code = code
    res.language = "micropython"
    return code, res, notes


def _add_devices(res, gen, board, dev, pins):
    """เพิ่มอุปกรณ์ (เช่น เซอร์โว 5 ตัวของมือหุ่นยนต์) ลงในภาพการต่อสาย ขาละ 1 ตัว"""
    cid, _, names = dev.partition(":")
    base = gen.kb.comp_by_id.get(cid.strip()) if hasattr(gen.kb, "comp_by_id") else None
    if base is None:
        base = next((c for c in gen.kb.components if c["id"] == cid.strip()), None)
    if base is None:
        return
    names = [n.strip() for n in names.split("|")] if names else []
    for i, pin in enumerate(pins):
        c = copy.deepcopy(base)
        c["icon"] = base["id"]                       # รูปวาดใช้ของอุปกรณ์ต้นแบบ
        c["id"] = "%s_%d" % (base["id"], len([x for x in res.components if x.get("icon") == base["id"]]) + 1)
        label = names[i] if i < len(names) else str(i + 1)
        c["name_th"] = "%s (%s)" % (base["name_th"], label)
        c["name_en"] = "%s #%d %s" % (base["name_en"], i + 1, label)
        res.components.append(c)
        res.assigned[c["id"]] = {}
        for p in c["pins"]:
            if p["kind"] == "signal":
                res.assigned[c["id"]][p["role"]] = pin
                res.wiring.append(dict(comp=c["id"], comp_name=c["name_en"], comp_pin=p["label"],
                                       board_pin=board_pin_label(board, pin), kind="signal", pin=pin))
            else:
                res.wiring.append(dict(comp=c["id"], comp_name=c["name_en"], comp_pin=p["label"],
                                       board_pin=power_label(board, p["kind"]), kind=p["kind"], pin=None))
    if base.get("warnings"):
        res.warnings.append("%s: %s" % (base["name_en"], base["warnings"][0]))


def references_for(kb, ino_code):
    """คำสั่ง Arduino ที่ใช้ในโค้ด พร้อมวิธีเขียนใน MicroPython (ใช้แสดงคู่กับโค้ด C++)"""
    return kb.ref_for_code(ino_code)

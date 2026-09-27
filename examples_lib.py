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
"""
import json
import os
import re

from generator import Result, board_pin_label, pin_literal

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
        need, n = spec.split("*")
        pool = [p for p in board["pools"].get(need, []) if p not in used and p not in board.get("serial_pins", [])]
        pins = pool[:int(n)]
        if len(pins) < int(n):
            notes.append("บอร์ด %s มีขาว่างไม่พอ ต้องการ %s ขา มี %d ขา" % (board["name"], n, len(pins)))
        used.update(pins)
        code = _set_const(code, const, "[%s]" % ", ".join(pin_literal(p) for p in pins))
        res.explanation.append("%s ต่อที่ขา %s" % (const, ", ".join(board_pin_label(board, p) for p in pins)))
    res.keys = list(dict.fromkeys(re.findall(r"print\(\s*[\"']([A-Za-z_]\w*)\s*:", code)))
    res.code = code
    res.language = "micropython"
    return code, res, notes


def references_for(kb, ino_code):
    """คำสั่ง Arduino ที่ใช้ในโค้ด พร้อมวิธีเขียนใน MicroPython (ใช้แสดงคู่กับโค้ด C++)"""
    return kb.ref_for_code(ino_code)

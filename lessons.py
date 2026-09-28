# -*- coding: utf-8 -*-
"""บทเรียนภาพเคลื่อนไหว (เพิ่มในเวอร์ชัน 2.4)

ไฟล์อยู่ในโฟลเดอร์ lessons/
  index.json      รายชื่อบทเรียน ชื่อไทย คำอธิบาย อุปกรณ์ที่เกี่ยวข้อง
  <ชื่อ>.html     หน้าเว็บภาพเคลื่อนไหว เปิดในเว็บเบราว์เซอร์ได้โดยไม่ต้องใช้อินเทอร์เน็ต

ครูเพิ่มบทเรียนใหม่ได้: วางไฟล์ .html ในโฟลเดอร์ lessons แล้วเพิ่มรายการใน index.json
"""
import json
import os
import pathlib
import sys
import webbrowser

from kb import BASE

FOLDER = os.path.join(BASE, "lessons")


def load():
    path = os.path.join(FOLDER, "index.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        items = json.load(f).get("lessons", [])
    return [x for x in items if os.path.exists(os.path.join(FOLDER, x["file"]))]


def by_id(lid):
    return next((x for x in load() if x["id"] == lid), None)


def search(query):
    q = query.lower().strip()
    out = []
    for x in load():
        hay = " ".join([x["title_th"], x.get("desc_th", ""), " ".join(x.get("components", []))]).lower()
        if not q or q in hay:
            out.append(x)
    return out


def open_lesson(lesson):
    """เปิดบทเรียนในเว็บเบราว์เซอร์ คืนค่า path ของไฟล์ (หรือ None ถ้าไม่พบ)"""
    if isinstance(lesson, str):
        lesson = by_id(lesson)
    if not lesson:
        return None
    path = os.path.abspath(os.path.join(FOLDER, lesson["file"]))
    if sys.platform == "win32":
        os.startfile(path)          # เปิดด้วยเบราว์เซอร์หลักของเครื่อง รองรับชื่อโฟลเดอร์ภาษาไทย
    else:
        webbrowser.open(pathlib.Path(path).as_uri())
    return path

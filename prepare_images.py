# -*- coding: utf-8 -*-
"""ตัวช่วยเตรียมรูปสำหรับคลังความรู้

วิธีใช้: คัดลอกรูปจากมือถือ (.jpg .jpeg .png .webp) ลงโฟลเดอร์ images
ตั้งชื่อไฟล์ตามรายชื่อใน images/รายชื่อรูปที่ต้องถ่าย.txt แล้วรัน:  python prepare_images.py
โปรแกรมจะย่อรูปและแปลงเป็น .png ให้ แล้วบอกว่ายังขาดรูปอะไรบ้าง
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(BASE, "images")
MAX_SIZE = 480


def wanted():
    items = []
    for f in ("boards", "components"):
        with open(os.path.join(BASE, "knowledge", f + ".json"), encoding="utf-8") as fp:
            for x in json.load(fp):
                stem = os.path.splitext(os.path.basename(x["image"]))[0]
                items.append((stem, x.get("name") or x.get("name_th")))
    return items


def main():
    try:
        from PIL import Image, ImageOps
    except ImportError:
        print("ต้องติดตั้ง Pillow ก่อน: pip install pillow")
        return
    converted = 0
    for name in os.listdir(IMG):
        stem, ext = os.path.splitext(name)
        if ext.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            continue
        src = os.path.join(IMG, name)
        dst = os.path.join(IMG, stem.lower() + ".png")
        try:
            im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        except Exception as e:  # noqa: BLE001
            print("เปิดรูปไม่ได้:", name, e)
            continue
        if ext.lower() == ".png" and max(im.size) <= MAX_SIZE and src == dst:
            continue
        im.thumbnail((MAX_SIZE, MAX_SIZE))
        im.save(dst)
        converted += 1
        if src != dst:
            os.remove(src)
        print("✔", name, "→", os.path.basename(dst), im.size)
    have = {os.path.splitext(n)[0] for n in os.listdir(IMG) if n.lower().endswith(".png")}
    missing = [(s, n) for s, n in wanted() if s not in have]
    print("\nแปลงรูปแล้ว %d รูป | มีรูปครบ %d จาก %d" % (converted, len(wanted()) - len(missing), len(wanted())))
    if missing:
        print("ยังขาดรูป:")
        for s, n in missing:
            print("  %-18s %s" % (s + ".png", n))


if __name__ == "__main__":
    main()

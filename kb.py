# -*- coding: utf-8 -*-
"""คลังความรู้บอร์ดและอุปกรณ์ (Knowledge Base)

ข้อมูลเก็บเป็นไฟล์ JSON ในโฟลเดอร์ knowledge/ ครูเพิ่มอุปกรณ์ใหม่ได้โดยแก้ไฟล์
components.json หรือ boards.json โดยไม่ต้องแก้โค้ดโปรแกรม
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))


NOT_DEVICE_WORDS = ["เจอ", "สายไฟ", "ไฟฟ้า", "จ่ายไฟ", "ไฟเลี้ยง", "แหล่งจ่าย"]


class KnowledgeBase:
    def __init__(self, folder=None):
        folder = folder or os.path.join(BASE, "knowledge")
        with open(os.path.join(folder, "boards.json"), encoding="utf-8") as f:
            self.boards = json.load(f)
        with open(os.path.join(folder, "components.json"), encoding="utf-8") as f:
            self.components = json.load(f)
        self.reindex()

    def reindex(self):
        self.board_by_id = {b["id"]: b for b in self.boards}
        self.comp_by_id = {c["id"]: c for c in self.components}
        # คำค้นยาวก่อน เพื่อให้ "ไฟ rgb" ถูกจับก่อน "ไฟ" และ "เปลวไฟ" ก่อน "ไฟ"
        self._keywords = sorted(
            ((kw.lower(), c) for c in self.components for kw in c["keywords"]),
            key=lambda x: -len(x[0]),
        )

    def image_path(self, item):
        p = item.get("image")
        if not p:
            return None
        stem = os.path.splitext(os.path.join(BASE, p))[0]
        for ext in (".png", ".gif", ".jpg", ".jpeg", ".webp", ".PNG", ".JPG", ".JPEG"):
            if os.path.exists(stem + ext):
                return stem + ext
        return None

    # ---------- โปรเจกต์ตัวอย่าง (knowledge/projects.json)
    def projects(self):
        path = os.path.join(BASE, "knowledge", "projects.json")
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    # ---------- เพิ่มอุปกรณ์ใหม่ลงไฟล์ components.json
    def save_component(self, comp):
        path = os.path.join(BASE, "knowledge", "components.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data = [c for c in data if c["id"] != comp["id"]] + [comp]
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
        self.components = data
        self.reindex()

    def delete_component(self, cid):
        path = os.path.join(BASE, "knowledge", "components.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data = [c for c in data if c["id"] != cid]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        self.components = data
        self.reindex()

    def detect(self, text):
        """หาอุปกรณ์ที่ถูกพูดถึงในคำสั่ง คืนค่าเป็นรายการ (อุปกรณ์, ตำแหน่งในข้อความ)"""
        low = text.lower()
        masked = low
        # คำที่มีคำค้นซ่อนอยู่ข้างใน แต่ไม่ได้หมายถึงอุปกรณ์ เช่น "เจอ" มี "จอ", "สายไฟ" มี "ไฟ"
        for w in NOT_DEVICE_WORDS:
            masked = masked.replace(w, "\0" * len(w))
        found = {}
        via = {}
        for kw, comp in self._keywords:
            start = 0
            while True:
                i = masked.find(kw, start)
                if i < 0:
                    break
                if comp["id"] not in found or i < found[comp["id"]][1]:
                    found[comp["id"]] = (comp, i)
                    via[comp["id"]] = kw
                masked = masked[:i] + ("\0" * len(kw)) + masked[i + len(kw):]
                start = i + len(kw)
        # "ให้รีเลย์เปิดไฟ" หมายถึงรีเลย์เปิดหลอดไฟดวงใหญ่ ไม่ได้หมายถึง LED อีกดวง
        if "relay" in found and via.get("led") == "ไฟ":
            found.pop("led")
        return sorted(found.values(), key=lambda x: x[1])

    def search(self, query):
        """ค้นหาอุปกรณ์และบอร์ดสำหรับหน้าคลังความรู้"""
        q = query.lower().strip()
        items = [("board", b) for b in self.boards] + [("comp", c) for c in self.components]
        if not q:
            return items
        out = []
        for kind, it in items:
            hay = " ".join([it.get("name", ""), it.get("name_th", ""), it.get("name_en", ""),
                            it.get("category", ""), " ".join(it.get("keywords", []))]).lower()
            if q in hay:
                out.append((kind, it))
        return out

    def context_for_ai(self, board, comps):
        """ย่อข้อมูลที่เกี่ยวข้องเพื่อส่งให้ AI (RAG)"""
        b = {k: board.get(k) for k in ("name", "family", "logic_v", "i2c", "input_only",
                                       "forbidden_list", "strapping", "adc2", "notes_th")}
        b["adc_pins"] = board["pools"].get("adc")
        cs = []
        for c in comps:
            cs.append({k: c.get(k) for k in ("name_th", "name_en", "voltage", "pins", "warnings",
                                             "setup", "read", "helpers", "library", "explain_th")})
        return json.dumps({"board": b, "components": cs}, ensure_ascii=False, indent=1)

# -*- coding: utf-8 -*-
"""ทดสอบรูปวาดอุปกรณ์และภาพการทำงาน (2.6): python test_visuals.py  (ต้องมีหน้าจอ)

1) วาดอุปกรณ์ทุกชนิดในคลังความรู้ และสั่งให้ขยับ ต้องไม่มีข้อผิดพลาด
2) ภาพการทำงานของทุกโปรเจกต์ ใส่ค่าจำลองแล้วขยับหลายรอบ ต้องไม่มีข้อผิดพลาด
"""
import tkinter as tk

import icons
from device import Simulator
from generator import CodeGenerator
from kb import KnowledgeBase
from scene import SceneCanvas

kb = KnowledgeBase()
gen = CodeGenerator(kb)
root = tk.Tk()
root.withdraw()
errors = []
root.report_callback_exception = lambda *a: errors.append(a[1])

c = tk.Canvas(root, width=200, height=200)
bad = 0
for comp in kb.components:
    try:
        d = icons.draw(c, comp["id"], 100, 100, 90, tag="t", comp=comp)
        for t in range(5):
            d.update(on=t % 2 == 0, value=t, t=t)
        if not icons.has_drawing(comp["id"]):
            print("ยังไม่มีรูปวาดเฉพาะ (ใช้รูปทั่วไป):", comp["id"])
    except Exception as e:  # noqa: BLE001
        bad += 1
        print("วาดไม่ได้:", comp["id"], e)
    c.delete("all")
print("icons-ok:", len(kb.components) - bad, "/", len(kb.components))

sc = SceneCanvas(root, width=1120, height=600)
sc.visible = True
bad = 0
for p in kb.projects():
    r = gen.generate(p["command"], "esp32-devkit")
    try:
        sc.load(r, kb.board_by_id["esp32-devkit"], p["command"])
        sim = Simulator(r, kb)
        for _ in range(12):
            vals = sim.step()
            sc.set_live(vals, sim.actuator_states(vals) or {a["id"]: True for a in r.components if a["type"] == "actuator"})
            sc._tick()
    except Exception as e:  # noqa: BLE001
        bad += 1
        print("ภาพการทำงานผิดพลาด:", p["id"], repr(e))
root.update()
print("scenes-ok:", len(kb.projects()) - bad - len(errors), "/", len(kb.projects()))
for e in errors[:5]:
    print("ข้อผิดพลาดระหว่างขยับ:", repr(e))
root.destroy()

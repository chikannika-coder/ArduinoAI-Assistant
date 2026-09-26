# -*- coding: utf-8 -*-
"""ทดสอบตัวสร้างโค้ด: python test_generator.py"""
from kb import KnowledgeBase
from generator import CodeGenerator, check_code

kb = KnowledgeBase()
gen = CodeGenerator(kb)
CASES = [
    ("esp32-devkit", "ให้ LED ขา 4 กระพริบทุก 2 วินาที"),
    ("esp32-devkit", "ให้ไฟบนบอร์ดกระพริบทุก 0.5 วินาที"),
    ("esp32-devkit", "หมุน Servo ขา 18 ไป 45 องศา"),
    ("esp32-devkit", "อ่านระยะทางด้วยอัลตราโซนิก ถ้าใกล้กว่า 15 ซม. ให้ Buzzer ดัง"),
    ("esp32-devkit", "อ่านอุณหภูมิและความชื้นด้วย DHT11 แล้วแสดงบนจอ OLED"),
    ("esp32-devkit", "ถ้าดินแห้งน้อยกว่า 30 ให้รีเลย์เปิดปั๊มน้ำ"),
    ("esp32-devkit", "ถ้ามีคนเคลื่อนไหวให้ไฟ LED ติด"),
    ("esp32-devkit", "ให้ LED ขา 34 กระพริบ"),
    ("esp32-devkit", "ให้ LED ขา 7 กระพริบ"),
    ("esp8266-nodemcu", "อ่านค่าแสง LDR และความชื้นในดิน"),
    ("pico", "ถ้าแก๊สมากกว่า 60 ให้บัซเซอร์ดัง และไฟ LED ติด"),
    ("arduino-uno", "อ่านระยะทาง ultrasonic trig 9 echo 10 ถ้าใกล้กว่า 20 ให้ servo ขา 6 หมุน 90 องศา"),
    ("esp32-devkit", "อ่านค่า BMP280"),
    ("esp32-devkit", "สวัสดีครับ"),
    ("esp32-devkit", "วัดค่า pH น้ำลายด้วย PH-4502C ถ้าน้อยกว่า 5.5 ให้ LED ติด"),
    ("esp32-devkit", "วัดไข้ด้วย MLX90614 แล้วแสดงบนจอ OLED"),
    ("esp32-devkit", "วัดชีพจรด้วย MAX30102 ถ้ามากกว่า 100 ให้ Buzzer ดัง"),
    ("esp32-devkit", "อ่านคลื่นสมองด้วย EEG ถ้ามากกว่า 2 ให้ LED ติด"),
    ("pico", "วัดระยะด้วยเลเซอร์ VL53L0X ถ้าใกล้กว่า 100 ให้ LED ติด"),
    ("esp32-cam", "ถ้า Sharp IR ใกล้กว่า 20 ให้ LED ติด"),
    ("arduino-uno", "อ่านคลื่นไฟฟ้าหัวใจด้วย AD8232"),
]
ok = 0
for board, cmd in CASES:
    r = gen.generate(cmd, board)
    errs, warns = check_code(r.code, kb.board_by_id[board]) if r.language == "micropython" else ([], [])
    print("=" * 70); print(board, "|", cmd)
    print(r.code)
    print("WIRING:", [(w["comp_name"], w["comp_pin"], w["board_pin"]) for w in r.wiring])
    print("ERR:", r.errors, "| CODECHECK:", errs); print("WARN:", r.warnings)
    print("RULE:", r.rule, "KEYS:", r.keys)
    if not errs:
        ok += 1
print("\nsyntax-ok:", ok, "/", len(CASES))


# ---- ตรวจคลังโปรเจกต์ และโค้ดตรวจสายของอุปกรณ์ทุกชิ้น
bad = 0
for p in kb.projects():
    r = gen.generate(p["command"], "esp32-devkit")
    ids = sorted(c["id"] for c in r.components)
    if ids != sorted(p["components"]) or r.errors or check_code(r.code, kb.board_by_id["esp32-devkit"])[0]:
        bad += 1
        print("โปรเจกต์มีปัญหา:", p["id"], ids, r.errors)
print("projects-ok:", len(kb.projects()) - bad, "/", len(kb.projects()))
bad = n = 0
for bid in ("esp32-devkit", "pico", "esp8266-nodemcu"):
    for c in kb.components:
        _, _, r = gen.plan(("อ่าน " if c["type"] == "sensor" else "") + c["keywords"][0], bid)
        if c["id"] not in r.assigned:
            continue
        n += 1
        try:
            compile(gen.test_code(c, r.assigned[c["id"]], kb.board_by_id[bid]), "test", "exec")
        except SyntaxError as e:
            bad += 1
            print("โค้ดตรวจสายผิด:", bid, c["id"], e)
print("wiring-tests-ok:", n - bad, "/", n)

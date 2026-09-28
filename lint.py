# -*- coding: utf-8 -*-
"""ตรวจโค้ด Arduino / Turbo C หาจุดที่นักเรียนมักเขียนผิด (เพิ่มในเวอร์ชัน 2.5)

ใช้ตอนเปิดไฟล์ .ino / .c ในแท็บ ① สร้างโค้ด
กฎมาจากจุดผิดที่พบจริงในโครงงานเกษตรอัจฉริยะ ทสรช. เช่น ใช้ขาซ้ำ อ่าน DHT ไม่ตรวจค่า ให้อาหารซ้ำทั้งชั่วโมง

check(code) คืนค่า (errors, warnings) เป็นข้อความภาษาไทย
"""
import re

PIN_NAME = re.compile(r"(PIN|RELAY|SERVO|TRIG|ECHO|LED|BUZZER|SENSOR|PUMP|FAN|HEAT|DOUT|SCK|MOTOR|BUS|^S[0-3]$|OUT)", re.I)
IGNORE_NAMES = re.compile(r"(VALUE|READING|STATE|THRESHOLD|TYPE|NUM_|ANGLE|TIME|DELAY|WEIGHT|SETPOINT|MAX|MIN|STEP|SPEED|COUNT)", re.I)


def _strip_comments(code):
    code = re.sub(r"/\*.*?\*/", " ", code, flags=re.S)
    return re.sub(r"//[^\n]*", " ", code)


def _pin_value(v, names):
    v = v.strip()
    if re.fullmatch(r"\d+", v):
        return int(v)
    if re.fullmatch(r"A\d{1,2}", v):
        return v
    return names.get(v)


def _pins(code):
    """คืน dict ขา -> รายชื่อผู้ใช้ขานั้น และ dict ชื่อค่าคงที่ -> ขา"""
    names = {}
    for m in re.finditer(r"#define\s+(\w+)\s+(A?\d+)\b", code):
        names[m.group(1)] = _pin_value(m.group(2), names)
    for m in re.finditer(r"(const\s+)?(?:int|byte|uint8_t)\s+(\w+)\s*=\s*(A?\d+)\s*;", code):
        # ตัวแปรธรรมดา เช่น int sensorValue = 0; ไม่ใช่เลขขา นับเฉพาะค่าคงที่ หรือชื่อที่มีคำว่า pin
        if m.group(1) or re.search(r"pin", m.group(2), re.I):
            names[m.group(2)] = _pin_value(m.group(3), names)
    users = {}

    def use(pin, who):
        if pin is None:
            return
        users.setdefault(pin, [])
        if who not in users[pin]:
            users[pin].append(who)

    for name, pin in names.items():
        if PIN_NAME.search(name) and not IGNORE_NAMES.search(name):
            use(pin, name)
    def counted(v):          # ชื่อค่าคงที่ที่นับไปแล้ว ไม่ต้องนับซ้ำเป็นอุปกรณ์อีกชื่อ
        v = v.strip()
        return v in names and PIN_NAME.search(v) and not IGNORE_NAMES.search(v)

    for m in re.finditer(r"LiquidCrystal\s+\w+\s*\(([^)]*)\)", code):
        for v in m.group(1).split(","):
            if not counted(v):
                use(_pin_value(v, names), "จอ LCD")
    for m in re.finditer(r"(HX711|SoftwareSerial)\s+\w+\s*\(([^)]*)\)", code):
        for v in m.group(2).split(","):
            if not counted(v):
                use(_pin_value(v, names), m.group(1))
    for m in re.finditer(r"\.attach\(\s*(\w+)\s*\)", code):
        v = _pin_value(m.group(1), names)
        if isinstance(m.group(1), str) and not re.fullmatch(r"A?\d+", m.group(1)):
            continue                 # attach(SERVO_PIN) นับจากชื่อค่าคงที่แล้ว
        use(v, "Servo")
    return users, names


def check(code):
    errors, warns = [], []
    src = _strip_comments(code)

    # ---- 1) ใช้ขาเดียวกันกับอุปกรณ์หลายชิ้น
    users, names = _pins(src)
    for pin, who in sorted(users.items(), key=lambda kv: str(kv[0])):
        real = [w for w in who if not (w in names and names.get(w) == pin and
                                       any(re.search(r"#define\s+%s\s+%s\b" % (w, o), src) for o in who if o != w))]
        if len(real) > 1:
            errors.append("🩺 ขา %s ถูกใช้ซ้ำ: %s (ต่อสายเข้าขาเดียวกันไม่ได้ ต้องย้ายอุปกรณ์หนึ่งไปขาอื่น)"
                          % (pin, ", ".join(real)))
    if re.search(r"Serial\.begin", src):
        for p in (0, 1):
            if p in users:
                warns.append("🩺 ขา %d ใช้กับ %s แต่ขา 0/1 ใช้สื่อสารกับคอมพิวเตอร์ (Serial) อาจอัปโหลดไม่ได้"
                             % (p, ", ".join(users[p])))

    # ---- 2) ประกาศขาไว้แต่ไม่ได้ใช้
    unused = [n for n in names if PIN_NAME.search(n) and not IGNORE_NAMES.search(n)
              and len(re.findall(r"\b%s\b" % re.escape(n), src)) == 1]
    if unused:
        warns.append("🩺 ประกาศไว้แต่ไม่ได้ใช้: %s (ยังเขียนไม่เสร็จ หรือลบทิ้งได้)" % ", ".join(unused))

    # ---- 3) DHT
    if re.search(r"read(Temperature|Humidity)\s*\(", src) and "isnan" not in src:
        warns.append("🩺 อ่าน DHT แล้วไม่ได้ตรวจ isnan() ถ้าสายหลวมจะได้ค่า nan แล้วเงื่อนไขทำงานผิด")

    # ---- 4) เวลา
    for m in re.finditer(r"(?:\.|\b)hour\(\)\s*==\s*(\d+)", src):
        near = src[m.start():m.start() + 60]
        if "minute" not in near:
            warns.append("🩺 เงื่อนไข hour() == %s เป็นจริงตลอดทั้งชั่วโมง งานข้างในจะทำซ้ำทุกรอบ loop "
                         "ต้องจำไว้ว่าทำไปแล้ว (เช่น เก็บวันที่ทำล่าสุด)" % m.group(1))
            break
    long_delays = [int(x) for x in re.findall(r"delay\(\s*(\d+)\s*\)", src) if int(x) >= 10000]
    if re.search(r"minute\(\)\s*==\s*\d+", src) and any(d >= 60000 for d in long_delays):
        warns.append("🩺 เช็ก minute() == ... แต่ loop รอนาน 1 นาทีขึ้นไป บางวันอาจข้ามนาทีนั้นจนงานไม่ทำงาน")
    if long_delays:
        warns.append("🩺 delay(%d) บอร์ดหยุดรอ %d วินาที ระหว่างนั้นอ่านเซนเซอร์หรือกดปุ่มไม่ได้ "
                     "ลองใช้ millis() จับเวลาแทน" % (max(long_delays), max(long_delays) // 1000))

    # ---- 5) อัลตราโซนิก
    if re.search(r"pulseIn\s*\(\s*\w+\s*,\s*(HIGH|LOW)\s*\)", src):
        warns.append("🩺 pulseIn ไม่ได้กำหนดเวลารอ ถ้าไม่มีเสียงสะท้อน โปรแกรมจะค้างนาน 1 วินาที "
                     "ใส่ตัวที่ 3 เช่น pulseIn(ECHO, HIGH, 30000)")
    if "pulseIn" in src and re.search(r"(water|level)\w*\s*>\s*\d", src, re.I):
        warns.append("🩺 อัลตราโซนิกวัดระยะจากเซนเซอร์ถึงผิวน้ำ ระยะมาก = น้ำน้อย "
                     "ถ้าต้องการความลึกน้ำ ใช้ ความสูงถัง - ระยะที่วัดได้")

    # ---- 6) เซนเซอร์แอนะล็อกที่มักตีความผิด
    if re.search(r"(soil|moisture)\w*\s*<\s*\d+", src, re.I):
        warns.append("🩺 เซนเซอร์ความชื้นดินส่วนใหญ่ \"ยิ่งแห้งค่ายิ่งสูง\" ถ้าใช้ค่าน้อยแปลว่าดินแห้ง "
                     "ให้ทดสอบกับดินแห้งและดินเปียกจริงก่อนว่าค่าไปทางไหน")
    if re.search(r"(pH|DO|ph)\w*\s*=\s*analogRead\([^)]*\)\s*\*\s*\(?\s*5\.0", src):
        warns.append("🩺 ค่า pH / DO ที่คูณ 5.0/1023 ยังเป็นโวลต์ ไม่ใช่หน่วยจริง ต้องแปลงด้วยค่าปรับเทียบ "
                     "(ดูตัวอย่าง 📚 16 ShrimpPond)")
    if re.search(r"analogRead\(\s*COLOR", src, re.I):
        warns.append("🩺 เซนเซอร์สี TCS3200/TCS230 ไม่ใช่แอนะล็อก ใช้ analogRead ไม่ได้ ต้องใช้ pulseIn "
                     "(ดูตัวอย่าง 📚 16 FruitColor)")
    if re.search(r"lcd\.print", src) and not re.search(r"lcd\.(setCursor|clear|home)", src):
        warns.append("🩺 lcd.print() ต่อกันทุกรอบโดยไม่ setCursor()/clear() ข้อความจะต่อท้ายไปเรื่อย ๆ จนอ่านไม่ออก")
    if re.search(r"HX711", src) and re.search(r"set_scale\(\s*\)", src):
        warns.append("🩺 scale.set_scale() ไม่ได้ใส่ค่าปรับเทียบ น้ำหนักที่ได้ยังไม่ใช่กรัม")

    # ---- 7) รีเลย์
    if re.search(r"digitalWrite\(\s*\w*RELAY\w*\s*,\s*HIGH\s*\)", src, re.I):
        warns.append("🩺 โมดูลรีเลย์ส่วนใหญ่ทำงานเมื่อสั่ง LOW (Active LOW) ถ้าสั่ง HIGH แล้วรีเลย์ดับ ให้สลับ HIGH กับ LOW")

    # ---- 8) Turbo C พอร์ตขนาน
    if re.search(r"\b(outportb?|inportb?)\s*\(", src):
        warns.append("🩺 โค้ด Turbo C คุมพอร์ตขนาน: outport(0x378, ค่า) = ส่งค่า 8 บิตออกขา D0-D7, "
                     "inportb(0x379) & มาสก์ = อ่านขาสถานะ S3-S7 ดูวิธีเขียนใน MicroPython ที่ 📚 หมวด 17 และตารางคำสั่งด้านล่าง")
    return errors, warns

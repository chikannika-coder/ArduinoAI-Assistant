# มือหุ่นยนต์ 5 นิ้ว รับคำสั่งทางสาย USB (RobotHandSerial)
# ต้นฉบับ C++: arduino_examples/18.RobotHand/RobotHandSerial/RobotHandSerial.ino  (แก้จาก pan_robot_hand2.ino ของครู)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# ขาเพิ่ม: SERVO_PINS=pwm*5@servo:โป้ง|ชี้|กลาง|นาง|ก้อย
#
# ใช้กับหน้าเว็บควบคุมด้วยกล้อง (แท็บ ⑤ → 🎬 มือหุ่นยนต์ควบคุมด้วยกล้อง) หรือพิมพ์คำสั่งเองใน Thonny
# อัปโหลดเป็น main.py แล้วปิด Thonny ก่อนต่อจากหน้าเว็บ (ใช้พอร์ตพร้อมกันไม่ได้)
#
# คำสั่งที่รับ (หนึ่งคำสั่งต่อบรรทัด) เหมือนของเดิมทุกคำสั่ง และรับรูปแบบของหน้าเว็บด้วย
#   T:45                       นิ้วเดียว (T I M R P = โป้ง ชี้ กลาง นาง ก้อย) มุม 0-90
#   ALL:T45,I30,M60,R20,P90    ทุกนิ้วพร้อมกัน
#   A:180,0,180,0,0            จากหน้าเว็บเดิม: 180 = นิ้วเหยียด, 0 = นิ้วงอ (แปลงเป็นมุม 0-90 ให้)
#   OPEN / CLOSE / TEST / SEQ:wave / SEQ:fist
#   STOP                       หยุดฉุกเฉิน: กางมือและไม่รับคำสั่งขยับ จนกว่าจะส่ง RESUME
#   HB                         สัญญาณชีพ (heartbeat) บอกว่าผู้ควบคุมยังอยู่
#
# สิ่งที่เพิ่มจากของเดิม
#   1) ของเดิมไม่รับรูปแบบ A:... ที่หน้าเว็บส่งมา มือจึงไม่ขยับ ตอนนี้รับได้ทั้งสองแบบ
#   2) Fail-safe: ถ้าไม่มีคำสั่งเกิน TIMEOUT_MS (โปรแกรมบนคอมพ์ค้าง/สายหลุด) มือจะกางออกเอง
#   3) E-Stop (STOP/RESUME) ตามหลักสูตรควบคุมแขนกลระยะไกล
#
# ⚠ เซอร์โว 5 ตัวกินกระแสรวมได้ถึง 2-3 แอมป์ ต้องใช้แหล่งจ่าย 5V แยก และต่อ GND ร่วมกับบอร์ด
#   ห้ามเลี้ยงเซอร์โวจากขา 3V3 / 5V ของบอร์ด (บอร์ดจะรีเซ็ตเองตอนนิ้วขยับพร้อมกัน)
from machine import Pin, PWM
import sys
import select
import time

SERVO_PINS = [4, 18, 19, 23, 25]   # [โป้ง, ชี้, กลาง, นาง, ก้อย]
MIN_ANGLE = 0                      # นิ้วเหยียด (มือกาง)
MAX_ANGLE = 90                     # นิ้วงอสุด (กำมือ) ปรับตามกลไกจริง อย่าให้สายเอ็นตึงเกิน
TIMEOUT_MS = 3000                  # ไม่มีคำสั่งนานเท่านี้ -> กางมือ (0 = ปิดระบบนี้)
NAMES = "TIMRP"

servos = [PWM(Pin(p), freq=50) for p in SERVO_PINS]
angles = [0, 0, 0, 0, 0]
stopped = False


def write(i, angle):
    angle = max(MIN_ANGLE, min(MAX_ANGLE, int(angle)))          # = constrain() ของ Arduino
    servos[i].duty_u16((500 + angle * 2000 // 180) * 65535 // 20000)
    angles[i] = angle


def open_all():
    for i in range(5):
        write(i, MIN_ANGLE)


def close_all():
    for i in range(5):
        write(i, MAX_ANGLE)


def wave():
    for i in (4, 3, 2, 1, 0):                  # ก้อย -> โป้ง
        write(i, MAX_ANGLE)
        time.sleep_ms(200)
        write(i, MIN_ANGLE)
        time.sleep_ms(200)


def handle(cmd):
    """แปลคำสั่งหนึ่งบรรทัด คืนค่า True ถ้าเข้าใจคำสั่ง"""
    global stopped
    cmd = cmd.strip().upper()
    if not cmd:
        return False
    if cmd == "STOP":
        stopped = True
        open_all()
        print("E-STOP")
        return True
    if cmd == "RESUME":
        stopped = False
        print("RESUMED")
        return True
    if cmd == "HB":
        return True
    if stopped:
        return True                               # หยุดฉุกเฉินอยู่: ไม่ขยับตามคำสั่ง
    try:
        if len(cmd) >= 3 and cmd[1] == ":" and cmd[0] in NAMES:
            write(NAMES.index(cmd[0]), int(cmd[2:]))
        elif cmd.startswith("ALL:"):
            for part in cmd[4:].split(","):
                part = part.strip()
                if len(part) >= 2 and part[0] in NAMES:
                    write(NAMES.index(part[0]), int(part[1:]))
        elif cmd.startswith("A:"):
            for i, v in enumerate(cmd[2:].split(",")[:5]):
                v = max(0, min(180, int(v)))       # 180 = เหยียด -> MIN_ANGLE, 0 = งอ -> MAX_ANGLE
                write(i, MAX_ANGLE - v * (MAX_ANGLE - MIN_ANGLE) // 180)
        elif cmd in ("OPEN", "SEQ:OPEN"):
            open_all()
        elif cmd == "CLOSE":
            close_all()
        elif cmd == "SEQ:WAVE":
            wave()
        elif cmd == "SEQ:FIST":
            close_all()
            time.sleep(1)
            open_all()
        elif cmd in ("TEST", "SEQ:TEST"):
            for i in range(5):
                print("ทดสอบนิ้ว", "โป้ง ชี้ กลาง นาง ก้อย".split()[i])
                write(i, MAX_ANGLE)
                time.sleep_ms(500)
                write(i, MIN_ANGLE)
                time.sleep_ms(500)
        else:
            print("ERR ไม่รู้จักคำสั่ง:", cmd)
            return False
    except ValueError:
        print("ERR ตัวเลขผิด:", cmd)
        return False
    return True


open_all()                                         # เริ่มด้วยมือกาง (ปลอดภัย)
print("AI HAND CONTROLLER - READY")
poll = select.poll()
poll.register(sys.stdin, select.POLLIN)
buf = ""
last_cmd = time.ticks_ms()
safe = True
n = 0
while True:
    while poll.poll(0):                            # อ่านตัวอักษรที่ส่งมาทาง USB (ไม่หยุดรอ)
        ch = sys.stdin.read(1)
        if ch in ("\n", "\r"):
            if handle(buf):
                last_cmd = time.ticks_ms()
                safe = False
            buf = ""
        else:
            buf += ch
    if TIMEOUT_MS and not safe and time.ticks_diff(time.ticks_ms(), last_cmd) > TIMEOUT_MS:
        open_all()                                 # ผู้ควบคุมหายไป: กางมือไว้ก่อน
        safe = True
        print("TIMEOUT ไม่มีคำสั่ง กางมือแล้ว")
    n += 1
    if n % 50 == 0:                                # ส่งมุมนิ้วออกมาทำกราฟทุก ~0.5 วินาที
        for name, a in zip(("thumb", "index", "middle", "ring", "pinky"), angles):
            print("%s:" % name, a)
    time.sleep_ms(10)

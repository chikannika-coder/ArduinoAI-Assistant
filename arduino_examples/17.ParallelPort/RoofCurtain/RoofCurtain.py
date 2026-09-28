# จาก Turbo C พอร์ตขนาน สู่ MicroPython: หลังคาและม่านอัตโนมัติ (RoofCurtain)
# ต้นฉบับ Turbo C: arduino_examples/17.ParallelPort/RoofCurtain/RoofCurtain.c  (โครงงาน Roof ของครู)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# ขาเพิ่ม: DATA_PINS=out*8, S4_PIN=inpu, S5_PIN=inpu, S6_PIN=inpu, S7_PIN=inpu
#
# แปลงแบบ "เก็บตรรกะเดิมไว้ทั้งหมด": เขียนฟังก์ชัน outport() และ inportb() เลียนแบบพอร์ตขนาน
# แล้วโค้ดส่วนควบคุม (CheckRain, CheckSunny, DriveCurtain, DriveRoof) แทบเหมือนของเดิมทุกบรรทัด
#
# ต่อสาย (เหมือนพอร์ตขนานเดิม แค่ย้ายมาต่อที่บอร์ด)
#   DATA_PINS[0..3] = D0-D3 -> ULN2003 สเต็ปมอเตอร์ม่าน IN1-IN4      (ขั้น 1, 2, 4, 8 = ทีละขด)
#   DATA_PINS[4..7] = D4-D7 -> ULN2003 สเต็ปมอเตอร์หลังคา IN1-IN4    (ขั้น 48, 96, 192, 144 = ทีละ 2 ขด)
#   S4_PIN = เซนเซอร์แสง (0 = แดดจ้า)      S5_PIN = เซนเซอร์ฝน (1 = ฝนตก)
#   S6_PIN = สวิตช์ปลายทาง ม่านปิดสุด (กดแล้วเป็น 0)   S7_PIN = สวิตช์ปลายทาง ม่านเปิดสุด (กดแล้วเป็น 0 บิต 7 กลับค่าเป็น 1)
# สเต็ปมอเตอร์ใช้ไฟ 5V แยก ต่อ GND ร่วมกับบอร์ด
#
# สิ่งที่แก้จากต้นฉบับ
#   1) DriveCurtain วนรอสวิตช์ปลายทางไม่มีที่สิ้นสุด ถ้าสวิตช์เสียมอเตอร์จะหมุนไม่หยุด เพิ่มจำนวนก้าวสูงสุด
#   2) ส่วนกราฟิกเมนู (graphics.h) ตัดออก ใช้ข้อความใน Serial แทน
from machine import Pin
import time

DATA_PINS = [4, 18, 19, 23, 25, 26, 13, 14]
S4_PIN = 27
S5_PIN = 32
S6_PIN = 33
S7_PIN = 34
DELAY = 3                    # มิลลิวินาทีต่อก้าว (เหมือน #define DELAY 3)
MAX_STEPS = 4000             # กันมอเตอร์ม่านหมุนไม่หยุด
OPEN, CLOSE = 1, 0

data = [Pin(p, Pin.OUT, value=0) for p in DATA_PINS]
status = {4: Pin(S4_PIN, Pin.IN, Pin.PULL_UP), 5: Pin(S5_PIN, Pin.IN, Pin.PULL_UP),
          6: Pin(S6_PIN, Pin.IN, Pin.PULL_UP), 7: Pin(S7_PIN, Pin.IN, Pin.PULL_UP)}

def outport(value):
    """แทน outport(0x378, value) ของ Turbo C: บิต 0 ของค่า -> D0, บิต 1 -> D1, ..."""
    for i, pin in enumerate(data):
        pin.value((value >> i) & 1)


def inportb():
    """แทน inportb(0x379): รวมขาสถานะเป็นเลข 8 บิต S3=8, S4=16, S5=32, S6=64, S7=128
    ขาที่ไม่ได้ต่ออ่านได้ 1 เหมือนพอร์ตจริง (ตัวต้านทานดึงขึ้น) และบิต 7 กลับค่าเหมือนขา BUSY ของพอร์ตจริง"""
    v = 0
    for bit, pin in status.items():
        b = pin.value()
        v |= (1 - b if bit == 7 else b) << bit
    return v


def Inport_():
    """ของเดิมอ่านซ้ำ 1000 ครั้งแล้วเลือกค่าที่เจอบ่อยที่สุด (กันสัญญาณกระตุก) ย่อเหลือ 15 ครั้ง"""
    counts = {}
    for _ in range(15):
        v = inportb()
        counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def CheckRain():
    return (Inport_() & 32) == 32          # BIT 5 ของ 0x379


def CheckSunny():
    return (Inport_() & 16) == 0           # BIT 4 ของ 0x379


def Status_Curtain():
    i = Inport_()
    if (i & 128) == 128:
        return 1                           # เปิดสุดแล้ว
    if (i & 64) == 0:
        return -1                          # ปิดสุดแล้ว
    return 0                               # กำลังเปิด/ปิด


step = 0
step2 = 0
Status_Roof = OPEN


def DriveCurtain(status_):
    global step
    Step_Curtain = [1, 2, 4, 8]
    goal = 1 if status_ == OPEN else -1
    n = 0
    while Status_Curtain() != goal and n < MAX_STEPS:
        outport(Step_Curtain[step])
        step = (step + (1 if status_ == OPEN else -1)) % 4   # ของเดิมใช้ if เช็กเกินขอบ ใช้ % แทนได้
        time.sleep_ms(DELAY)
        n += 1
    outport(0)


def DriveRoof(status_):
    global step2, Status_Roof
    Step_Roof = [16 + 32, 32 + 64, 64 + 128, 128 + 16]
    for _ in range(1000):                  # หลังคาไม่มีสวิตช์ปลายทาง ใช้จำนวนก้าวคงที่เหมือนของเดิม
        outport(Step_Roof[step2])
        step2 = (step2 + (1 if status_ == OPEN else -1)) % 4
        time.sleep_ms(2 * DELAY if status_ == OPEN else DELAY)
    outport(0)
    Status_Roof = status_


def OutportCenter():
    """เหมือนของเดิม: ทำให้ม่านตรงกับแสง และหลังคาตรงกับฝน"""
    sunny, st = CheckSunny(), Status_Curtain()
    if sunny and st != -1:
        DriveCurtain(CLOSE)
    elif not sunny and st != 1:
        DriveCurtain(OPEN)
    rain = CheckRain()
    if rain and Status_Roof == OPEN:
        DriveRoof(CLOSE)
    elif not rain and Status_Roof == CLOSE:
        DriveRoof(OPEN)


while True:
    OutportCenter()
    print("rain:", 1 if CheckRain() else 0)
    print("sunny:", 1 if CheckSunny() else 0)
    print("roof_open:", Status_Roof)
    time.sleep_ms(500)

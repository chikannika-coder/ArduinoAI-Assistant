# จาก Turbo C พอร์ตขนาน สู่ MicroPython: ราวตากผ้าอัตโนมัติ (ClothLine)
# ต้นฉบับ Turbo C: arduino_examples/17.ParallelPort/ClothLine/ClothLine.c  (โครงงาน ClothLine / ROWTAKPH.C ของครู)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# ขาเพิ่ม: DATA_PINS=out*7, S3_PIN=inpu, S5_PIN=inpu, S7_PIN=inpu
#
# การทำงานของเดิม: ฝนตก หรือไม่มีแดด -> เก็บราวเข้าที่ร่ม (door = 0) และเปิดพัดลมเป่าผ้า (fan = 1)
#                  แดดดีและไม่มีฝน -> เลื่อนราวออกไปตากแดด (door = 1) ปิดพัดลม
# ต่อสาย
#   DATA_PINS[0..3] = D0-D3 -> ULN2003 สเต็ปมอเตอร์เลื่อนราว (ขั้น 5, 6, 10, 9 = เต็มก้าว 2 ขด)
#   DATA_PINS[6]    = D6    -> รีเลย์/ทรานซิสเตอร์พัดลม (outport(0x378, 64))
#   S5_PIN = เซนเซอร์แสง (1 = ไม่มีแดด)   S7_PIN = เซนเซอร์ฝน (ต่อลงดินเมื่อไม่มีฝน)
#   S3_PIN = สวิตช์ปลายทาง (ราวเลื่อนถึงสุดทาง กดแล้วเป็น 0)
#
# สิ่งที่แก้จากต้นฉบับ
#   1) ดัชนีลำดับขั้นเกินขอบ: ของเดิมเช็ก if (j > 3) หลัง j++ ทำให้ใช้ Step[4] ซึ่งไม่มีอยู่ (และ Step[-1] ตอนถอย)
#      ใช้ j = (j + 1) % 4 แทน
#   2) ของเดิมหยุดมอเตอร์เมื่อ inportb(0x379) == 143 คือต้องให้ทุกขาอยู่ในสถานะเดียวพร้อมกัน
#      ถ้าฝนหยุดระหว่างเลื่อน ค่าจะไม่ใช่ 143 มอเตอร์หมุนไม่หยุด ใช้สวิตช์ปลายทาง S3 + จำนวนก้าวสูงสุดแทน
#   3) ของเดิมสั่งพัดลมด้วย outport(0x378, 64) ซึ่งเขียนทับบิตของมอเตอร์ด้วย ตัวอย่างนี้เก็บสถานะพัดลมไว้แล้วรวมบิต
from machine import Pin
import time

DATA_PINS = [4, 18, 19, 23, 25, 26, 13]
S3_PIN = 27
S5_PIN = 32
S7_PIN = 33
MAX_STEPS = 3000
FAN_BIT = 64                 # D6

data = [Pin(p, Pin.OUT, value=0) for p in DATA_PINS]
status = {3: Pin(S3_PIN, Pin.IN, Pin.PULL_UP), 5: Pin(S5_PIN, Pin.IN, Pin.PULL_UP),
          7: Pin(S7_PIN, Pin.IN, Pin.PULL_UP)}

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


door, fan = 1, 0
fan_out = 0


def Readport():
    """เหมือน Readport() ของเดิม: ดูฝนกับแดด แล้วตัดสินใจ door / fan"""
    value = inportb()
    rain = 0 if (value & 128) == 128 else 1
    sunny = 0 if (value & 32) == 32 else 1
    if rain or not sunny:
        return 0, 1, rain, sunny           # เก็บราว เปิดพัดลม
    return 1, 0, rain, sunny               # เลื่อนราวออก ปิดพัดลม


def Control_Door(action):
    Step = [5, 6, 10, 9]
    j = 0
    time.sleep_ms(300)                     # รอให้สวิตช์ปลายทางเดิมหลุดก่อน
    for n in range(MAX_STEPS):
        outport(Step[j] | fan_out)
        j = (j + 1) % 4 if action else (j - 1) % 4
        time.sleep_ms(3)
        if n > 50 and (inportb() & 8) == 0:  # S3 = 0: ถึงสุดทางแล้ว
            break
    outport(fan_out)


def Control_Fan(action):
    global fan_out
    fan_out = FAN_BIT if action else 0
    outport(fan_out)


while True:
    new_door, new_fan, rain, sunny = Readport()
    if new_door != door:
        door = new_door
        Control_Door(door)
    if new_fan != fan:
        fan = new_fan
        Control_Fan(fan)
    print("rain:", rain)
    print("sunny:", sunny)
    print("door:", door)
    time.sleep_ms(500)

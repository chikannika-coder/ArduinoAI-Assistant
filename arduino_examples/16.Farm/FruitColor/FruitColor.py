# ตัวอย่างเกษตรอัจฉริยะ: วัดความสุกของผลไม้ด้วยเซนเซอร์สี TCS3200 (FruitColor)
# ต้นฉบับ C++: arduino_examples/16.Farm/FruitColor/FruitColor.ino  (โครงงาน ทสรช.: เครื่องตรวจวัดความสุกของผลไม้ด้วยเซนเซอร์วัดค่าสี ร.ร.ราชประชานุเคราะห์ 53)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# ขาเพิ่ม: S0=out, S1=out, S2=out, S3=out, OUT_PIN=inp
#
# ต่อสาย TCS3200: VCC -> 3V3, GND -> GND, OE -> GND, S0 S1 S2 S3 OUT -> ขาตามตัวแปรด้านล่าง
# (ตัวอย่างนี้ไม่มีภาพการต่อสาย เพราะ TCS3200 ใช้ 5 ขา ให้ต่อตามรายการขาในช่องคำอธิบาย)
#
# สิ่งที่แก้จากต้นฉบับ
#   ไฟล์ Measure_the_ripeness_of_fruit.ino อ่านเซนเซอร์สีด้วย analogRead ซึ่งอ่าน TCS3200 ไม่ได้
#   ไฟล์ fruit.ino (จาก Random Nerd Tutorials) อ่านถูกวิธีแล้ว ตัวอย่างนี้แปลงจากไฟล์นั้น และเพิ่มการตัดสินว่าสุกหรือยัง
#
# วิธีปรับเทียบ: วางผลไม้ดิบ ดูค่า red/green ในกราฟ แล้ววางผลที่สุก ตั้ง RIPE_RATIO ให้อยู่ระหว่างสองค่า
from machine import Pin, time_pulse_us
import time

S0 = 25
S1 = 26
S2 = 27
S3 = 14
OUT_PIN = 34
RIPE_RATIO = 1.2             # สีแดงเข้มกว่าเขียวเกินกี่เท่าจึงถือว่าสุก (มะเขือเทศ มะม่วงบางพันธุ์)

s0, s1, s2, s3 = (Pin(p, Pin.OUT) for p in (S0, S1, S2, S3))
out = Pin(OUT_PIN, Pin.IN)
s0.value(1)                  # ตั้งความถี่ขาออก 20% (S0=1, S1=0)
s1.value(0)


def read_color(a, b):
    """เลือกฟิลเตอร์สีด้วย S2 S3 แล้ววัดความกว้างพัลส์ต่ำ (ยิ่งสั้น = สีนั้นยิ่งเข้ม)"""
    s2.value(a)
    s3.value(b)
    time.sleep_ms(20)
    t = time_pulse_us(out, 0, 100000)
    return t if t > 0 else 100000


while True:
    red = read_color(0, 0)
    green = read_color(1, 1)
    blue = read_color(0, 1)
    ratio = green / red          # พัลส์สั้น = สีเข้ม จึงเอาเขียวหารแดง ได้ค่ามาก = แดงเด่น
    print("red:", red)
    print("green:", green)
    print("blue:", blue)
    print("ripe:", 1 if ratio > RIPE_RATIO else 0)
    time.sleep_ms(300)

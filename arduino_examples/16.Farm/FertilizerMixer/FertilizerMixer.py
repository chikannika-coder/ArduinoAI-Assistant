# ตัวอย่างเกษตรอัจฉริยะ: เครื่องผสมปุ๋ยน้ำอัตโนมัติด้วยตาชั่ง (FertilizerMixer)
# ต้นฉบับ C++: arduino_examples/16.Farm/FertilizerMixer/FertilizerMixer.ino  (โครงงาน ทสรช.: ต้นแบบเครื่องจำลองการผสมปุ๋ยอัตโนมัติ Ai v.2 ร.ร.วัดไผ่ดำ)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: ชั่งน้ำหนักด้วย HX711 ให้รีเลย์ทำงาน
# ขา: hx711.DT=HX_DT, hx711.SCK=HX_SCK, relay.SIG=PUMP_A
# ขาเพิ่ม: PUMP_B=out, START_BTN=inpu
#
# สิ่งที่แก้จากต้นฉบับ
#   1) ต้นฉบับต่อจอ LCD ที่ขา 12, 11, 5, 4, 3, 2 ซ้ำกับ HX711 (ขา 4, 5) และปั๊ม (ขา 2, 3) อุปกรณ์จึงทำงานไม่ได้
#      ตัวอย่างนี้ให้โปรแกรมเลือกขาที่ไม่ซ้ำ และแสดงผลทางกราฟ (ถ้าต้องการจอ ใช้จอ OLED หรือ LCD แบบ I2C)
#   2) ต้นฉบับยังไม่มีขั้นตอนผสม ตัวอย่างนี้ทำเป็น "เครื่องสถานะ": รอ -> ปั๊มปุ๋ย A -> ปั๊มปุ๋ย B -> เสร็จ
#   3) กันปั๊มเดินไม่หยุด: ถ้าน้ำหนักไม่เพิ่มภายในเวลาที่กำหนด (ปุ๋ยหมด/ท่อตัน) ให้หยุดทันที
#
# ปั๊มรีดท่อ (peristaltic) ต่อผ่านรีเลย์และใช้ไฟแยก กดปุ่ม START เพื่อเริ่มผสม 1 ครั้ง
from machine import Pin
import time

HX_DT = 27
HX_SCK = 4
PUMP_A = 18
PUMP_B = 19
START_BTN = 23
HX_SCALE = 420.0             # ปรับตอน calibrate: วางของรู้น้ำหนัก แล้วแก้จนอ่านได้ตรง
AMOUNT_A = 200               # กรัม ของปุ๋ยสูตร A
AMOUNT_B = 100               # กรัม ของปุ๋ยสูตร B
STALL_S = 20                 # ถ้า 20 วินาทีน้ำหนักไม่เพิ่ม ถือว่าผิดปกติ
RELAY_ON, RELAY_OFF = 0, 1

hx_dt = Pin(HX_DT, Pin.IN)
hx_sck = Pin(HX_SCK, Pin.OUT, value=0)
pump_a = Pin(PUMP_A, Pin.OUT, value=RELAY_OFF)
pump_b = Pin(PUMP_B, Pin.OUT, value=RELAY_OFF)
button = Pin(START_BTN, Pin.IN, Pin.PULL_UP)


def hx_raw():
    t = time.ticks_ms()
    while hx_dt.value():                 # รอจน HX711 พร้อม
        if time.ticks_diff(time.ticks_ms(), t) > 1000:
            return None
    v = 0
    for _ in range(24):
        hx_sck.value(1)
        hx_sck.value(0)
        v = (v << 1) | hx_dt.value()
    hx_sck.value(1)
    hx_sck.value(0)
    if v & 0x800000:
        v -= 0x1000000
    return v


def hx_avg(n=5):
    vals = [x for x in (hx_raw() for _ in range(n)) if x is not None]
    return sum(vals) // len(vals) if vals else 0


offset = hx_avg(15)                      # ตั้งศูนย์ตอนเปิดเครื่อง (วางภาชนะเปล่าไว้ก่อน)


def weight():
    return round((hx_avg(5) - offset) / HX_SCALE, 1)


state = "รอ"
target = 0
best, best_time = 0, time.ticks_ms()
while True:
    w = weight()
    if state == "รอ" and button.value() == 0:
        offset = hx_avg(15)              # ตั้งศูนย์ใหม่ก่อนผสมทุกครั้ง
        state, target = "ปุ๋ย A", AMOUNT_A
        best, best_time = 0, time.ticks_ms()
    elif state == "ปุ๋ย A" and w >= target:
        state, target = "ปุ๋ย B", AMOUNT_A + AMOUNT_B
    elif state == "ปุ๋ย B" and w >= target:
        state = "เสร็จ"
    if state in ("ปุ๋ย A", "ปุ๋ย B"):
        if w > best + 2:                 # น้ำหนักยังเพิ่มอยู่
            best, best_time = w, time.ticks_ms()
        elif time.ticks_diff(time.ticks_ms(), best_time) > STALL_S * 1000:
            state = "หยุดฉุกเฉิน"
            print("น้ำหนักไม่เพิ่ม ปุ๋ยหมดหรือท่อตัน")
    pump_a.value(RELAY_ON if state == "ปุ๋ย A" else RELAY_OFF)
    pump_b.value(RELAY_ON if state == "ปุ๋ย B" else RELAY_OFF)
    if state in ("เสร็จ", "หยุดฉุกเฉิน") and button.value() == 0:
        state = "รอ"
        time.sleep_ms(500)
    print("weight_g:", w)
    print("สถานะ", state)
    time.sleep_ms(200)

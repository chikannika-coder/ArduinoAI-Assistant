# ตัวอย่างเกษตรอัจฉริยะ: สมาร์ทฟาร์มรดน้ำอัตโนมัติ (SmartFarm)
# ต้นฉบับ C++: arduino_examples/16.Farm/SmartFarm/SmartFarm.ino  (โครงงาน ทสรช.: สมาร์ทฟาร์มโรงเรือนอัจฉริยะ)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: อ่านค่า DHT22 และความชื้นในดิน ให้รีเลย์ทำงาน
# ขา: dht22.SIG=DHT_PIN, soil.SIG=SOIL_PIN, relay.SIG=PUMP_PIN
#
# สิ่งที่แก้จากต้นฉบับ
#   1) ต้นฉบับถือว่า analogRead < 300 = ดินแห้ง แต่เซนเซอร์ความชื้นดินส่วนใหญ่ "ยิ่งแห้งค่ายิ่งสูง"
#      ตัวอย่างนี้แปลงเป็น % ความชื้น (ดินเปียก = ค่าสูง) ก่อน แล้วทดสอบกับดินจริงว่าค่าไปทางไหน
#   2) ต้นฉบับหยุดรอ 1 นาทีด้วย delay(60000) ระหว่างนั้นทำอะไรไม่ได้ ตัวอย่างนี้ใช้การจับเวลาแทน
#   3) อ่าน DHT22 พลาด (สายหลวม) โปรแกรมไม่ค้าง
#   4) รีเลย์ส่วนใหญ่ทำงานเมื่อสั่ง 0 (Active LOW)
from machine import Pin, ADC
import dht
import time

DHT_PIN = 27
SOIL_PIN = 34
PUMP_PIN = 4
DRY_PERCENT = 35             # ความชื้นดินต่ำกว่านี้ = แห้ง ต้องรดน้ำ
PUMP_SECONDS = 5             # รดน้ำครั้งละกี่วินาที
CHECK_EVERY_S = 60           # ตรวจดินทุกกี่วินาที
RELAY_ON, RELAY_OFF = 0, 1   # ถ้ารีเลย์ทำงานกลับด้าน ให้สลับ 0 กับ 1


def make_adc(pin):
    if pin == "A0":
        return ADC(0)
    adc = ADC(Pin(pin))
    if hasattr(adc, "atten"):
        adc.atten(ADC.ATTN_11DB)
    return adc


sensor = dht.DHT22(Pin(DHT_PIN))
soil_adc = make_adc(SOIL_PIN)
pump = Pin(PUMP_PIN, Pin.OUT, value=RELAY_OFF)


def soil_percent():
    """0 = แห้งสนิท, 100 = เปียกมาก (เซนเซอร์ส่วนใหญ่ค่าสูงเมื่อแห้ง จึงกลับค่า)"""
    return 100 - soil_adc.read_u16() * 100 // 65535


last_check = time.ticks_ms() - CHECK_EVERY_S * 1000
while True:
    try:
        sensor.measure()
        print("temp_c:", sensor.temperature())
        print("humidity:", sensor.humidity())
    except OSError:
        print("อ่าน DHT22 ไม่ได้ ตรวจสาย DATA")
    soil = soil_percent()
    print("soil:", soil)
    if time.ticks_diff(time.ticks_ms(), last_check) >= CHECK_EVERY_S * 1000:
        last_check = time.ticks_ms()
        if soil < DRY_PERCENT:
            pump.value(RELAY_ON)          # ดินแห้ง: รดน้ำช่วงสั้น ๆ แล้วรอให้น้ำซึม
            time.sleep(PUMP_SECONDS)
            pump.value(RELAY_OFF)
    time.sleep(2)                          # DHT22 อ่านได้ไม่เร็วกว่าทุก 2 วินาที

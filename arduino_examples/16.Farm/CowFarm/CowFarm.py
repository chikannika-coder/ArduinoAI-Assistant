# ตัวอย่างเกษตรอัจฉริยะ: ฟาร์มวัวอัจฉริยะ รางน้ำและพัดลม (CowFarm)
# ต้นฉบับ C++: arduino_examples/16.Farm/CowFarm/CowFarm.ino  (โครงงาน ทสรช.: ฟาร์มวัวอัจฉริยะ ร.ร.พระปริยัติธรรมวัดภูเก็ต)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: อ่านค่า DHT22 และระดับน้ำ ให้รีเลย์ทำงาน
# ขา: dht22.SIG=DHT_PIN, water_level.SIG=WATER_PIN, relay.SIG=RELAY_PUMP
# ขาเพิ่ม: RELAY_FAN=out
#
# สิ่งที่แก้จากต้นฉบับ
#   1) ปั๊มเติมน้ำ: ต้นฉบับเปิดเมื่อ < 300 ปิดเมื่อ >= 300 พอดี น้ำกระเพื่อมทำให้ปั๊มติด-ดับถี่
#      ตัวอย่างนี้เปิดเมื่อน้ำต่ำกว่า 30% และเติมจนถึง 70% จึงปิด
#   2) กันปั๊มเดินตัวเปล่า: ถ้าเติมนานเกิน 3 นาทีแต่น้ำไม่ขึ้น (ท่อหลุด/น้ำประปาไม่ไหล) ให้หยุดและเตือน
#   3) วัวเครียดจากความร้อนเมื่ออากาศร้อนและชื้น จึงใช้ทั้งอุณหภูมิและความชื้นตัดสินใจเปิดพัดลม
from machine import Pin, ADC
import dht
import time

DHT_PIN = 27
WATER_PIN = 34
RELAY_PUMP = 4
RELAY_FAN = 18
WATER_LOW, WATER_FULL = 30, 70      # % ของเซนเซอร์ระดับน้ำ
TEMP_FAN = 28                       # ร้อนกว่านี้เปิดพัดลม
HUMID_FAN = 80                      # หรืออุ่นเกิน 26 และชื้นกว่านี้ ก็เปิดพัดลม
MAX_FILL_S = 180                    # เติมน้ำนานสุดกี่วินาที
RELAY_ON, RELAY_OFF = 0, 1


def make_adc(pin):
    if pin == "A0":
        return ADC(0)
    adc = ADC(Pin(pin))
    if hasattr(adc, "atten"):
        adc.atten(ADC.ATTN_11DB)
    return adc


sensor = dht.DHT22(Pin(DHT_PIN))
water_adc = make_adc(WATER_PIN)
pump = Pin(RELAY_PUMP, Pin.OUT, value=RELAY_OFF)
fan = Pin(RELAY_FAN, Pin.OUT, value=RELAY_OFF)
filling = False
fill_start = 0
pump_fault = False

while True:
    water = water_adc.read_u16() * 100 // 65535
    if not pump_fault:
        if not filling and water < WATER_LOW:
            filling, fill_start = True, time.ticks_ms()
        elif filling and water >= WATER_FULL:
            filling = False
        elif filling and time.ticks_diff(time.ticks_ms(), fill_start) > MAX_FILL_S * 1000:
            filling, pump_fault = False, True
            print("เติมน้ำนานเกินไปแต่น้ำไม่ขึ้น ตรวจท่อและน้ำประปา แล้วกดปุ่ม RESET")
    pump.value(RELAY_ON if filling else RELAY_OFF)
    try:
        sensor.measure()
        t, h = sensor.temperature(), sensor.humidity()
        hot = t > TEMP_FAN or (t > TEMP_FAN - 2 and h > HUMID_FAN)
        fan.value(RELAY_ON if hot else RELAY_OFF)
        print("temp_c:", t)
        print("humidity:", h)
    except OSError:
        print("อ่าน DHT22 ไม่ได้")
    print("water:", water)
    time.sleep(2)

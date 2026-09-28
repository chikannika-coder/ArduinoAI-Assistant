# ตัวอย่างเกษตรอัจฉริยะ: โรงเรือนเพาะเห็ดอัจฉริยะ (MushroomHouse)
# ต้นฉบับ C++: arduino_examples/16.Farm/MushroomHouse/MushroomHouse.ino  (โครงงาน ทสรช.: โรงเรือนเพาะเห็ดอัจฉริยะ ร.ร.นันทบุรีวิทยา)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: อ่านค่า DHT22 และความชื้นในดิน ให้รีเลย์ทำงาน
# ขา: dht22.SIG=DHT_PIN, soil.SIG=SOIL_PIN, relay.SIG=RELAY_HEAT
# ขาเพิ่ม: RELAY_MIST=out, RELAY_PUMP=out, RELAY_FAN=out
#
# ภาพการต่อสายแสดงรีเลย์ตัวแรก (ฮีตเตอร์) รีเลย์อีก 3 ตัวต่อแบบเดียวกันที่ขา RELAY_MIST RELAY_PUMP RELAY_FAN
# ใช้แทนโครงงานที่โครงสร้างเหมือนกันได้: โรงเรือนขยายพันธุ์สับปะรด, โรงเพาะเห็ดแยกชนิด, โรงเพาะเห็ดฟาง
#
# สิ่งที่แก้จากต้นฉบับ
#   1) เพิ่ม "ช่วงกันสั่น" (hysteresis): ต้นฉบับเปิดฮีตเตอร์ที่ < 25.0 และปิดที่ >= 25.0 พอดี
#      ค่าที่แกว่ง 24.9 / 25.0 ทำให้รีเลย์ติด-ดับถี่จนเสียเร็ว ตัวอย่างนี้เปิดที่ 24 ปิดที่ 26
#   2) ต้นฉบับยังไม่มีพัดลม ตัวอย่างนี้เปิดพัดลมเมื่อร้อนเกิน (เห็ดต้องการอากาศถ่ายเท)
#   3) ความชื้นดินกลับค่าเหมือนตัวอย่าง SmartFarm และอ่าน DHT พลาดไม่ค้าง
from machine import Pin, ADC
import dht
import time

DHT_PIN = 27
SOIL_PIN = 34
RELAY_HEAT = 4
RELAY_MIST = 18
RELAY_PUMP = 19
RELAY_FAN = 23
TEMP_LOW, TEMP_HIGH = 24, 30        # ต่ำกว่า 24 เปิดฮีตเตอร์ / สูงกว่า 30 เปิดพัดลม
HUMID_LOW, HUMID_OK = 75, 85        # ต่ำกว่า 75% เปิดพ่นหมอก จนถึง 85% จึงปิด
SOIL_DRY, SOIL_OK = 35, 50          # ก้อนเชื้อ/วัสดุเพาะแห้ง
RELAY_ON, RELAY_OFF = 0, 1


def make_adc(pin):
    if pin == "A0":
        return ADC(0)
    adc = ADC(Pin(pin))
    if hasattr(adc, "atten"):
        adc.atten(ADC.ATTN_11DB)
    return adc


sensor = dht.DHT22(Pin(DHT_PIN))
soil_adc = make_adc(SOIL_PIN)
relays = {name: Pin(p, Pin.OUT, value=RELAY_OFF) for name, p in
          (("heat", RELAY_HEAT), ("mist", RELAY_MIST), ("pump", RELAY_PUMP), ("fan", RELAY_FAN))}
state = {name: False for name in relays}


def control(name, value, low, high, turn_on_when_low=True):
    """เปิด/ปิดแบบมีช่วงกันสั่น: เปิดเมื่อเลยเกณฑ์หนึ่ง ปิดเมื่อกลับมาถึงอีกเกณฑ์"""
    if turn_on_when_low:
        if value < low:
            state[name] = True
        elif value >= high:
            state[name] = False
    else:
        if value > high:
            state[name] = True
        elif value <= low:
            state[name] = False
    relays[name].value(RELAY_ON if state[name] else RELAY_OFF)


while True:
    try:
        sensor.measure()
        t, h = sensor.temperature(), sensor.humidity()
    except OSError:
        print("อ่าน DHT22 ไม่ได้ ปิดอุปกรณ์ทุกตัวไว้ก่อนเพื่อความปลอดภัย")
        for r in relays.values():
            r.value(RELAY_OFF)
        time.sleep(2)
        continue
    soil = 100 - soil_adc.read_u16() * 100 // 65535
    control("heat", t, TEMP_LOW, TEMP_LOW + 2)
    control("fan", t, TEMP_HIGH - 2, TEMP_HIGH, turn_on_when_low=False)
    control("mist", h, HUMID_LOW, HUMID_OK)
    control("pump", soil, SOIL_DRY, SOIL_OK)
    print("temp_c:", t)
    print("humidity:", h)
    print("soil:", soil)
    time.sleep(2)

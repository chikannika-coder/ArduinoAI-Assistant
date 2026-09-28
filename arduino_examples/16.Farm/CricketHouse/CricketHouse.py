# ตัวอย่างเกษตรอัจฉริยะ: ตู้เลี้ยงจิ้งหรีดอัตโนมัติ (CricketHouse)
# ต้นฉบับ C++: arduino_examples/16.Farm/CricketHouse/CricketHouse.ino  (โครงงาน ทสรช.: ตู้เลี้ยงจิ้งหรีดอัตโนมัติ ร.ร.ราชประชานุเคราะห์ 24)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: อ่านค่า DHT22 ให้รีเลย์ทำงาน
# ขา: dht22.SIG=DHT_PIN, relay.SIG=RELAY_HEAT
# ขาเพิ่ม: RELAY_FAN=out, RELAY_LIGHT=out, RELAY_FEED=out, RELAY_WATER=out
#
# สิ่งที่แก้จากต้นฉบับ
#   1) ต้นฉบับเปิดพัดลมเมื่อความชื้น "ต่ำ" กว่าค่าที่ตั้ง แต่พัดลมทำให้ความชื้นลดลงอีก
#      ตัวอย่างนี้เปิดพัดลมเมื่อชื้นเกินหรือร้อนเกิน
#   2) ต้นฉบับให้อาหารเมื่อ hour==8 และ minute==0 แต่รอบละ 1 นาทีพอดี (delay 60000 + เวลาอ่านเซนเซอร์)
#      บางวันจะข้ามนาทีนั้นไปจนไม่ได้ให้อาหาร ตัวอย่างนี้ให้ครั้งแรกที่ถึงชั่วโมงนั้นแล้วจำไว้ว่าให้แล้ว
#   3) ใช้นาฬิกาในบอร์ดแทน DS3231 (ถ้ามี DS3231 ให้ใช้ไลบรารี urtc อ่านเวลาแทน rtc.datetime())
from machine import Pin, RTC
import dht
import time

DHT_PIN = 27
RELAY_HEAT = 4
RELAY_FAN = 18
RELAY_LIGHT = 19
RELAY_FEED = 23
RELAY_WATER = 25
TEMP_SET = 28                    # จิ้งหรีดชอบอุ่นประมาณ 28-32 องศา
TEMP_HOT = 34
HUMID_HIGH = 75                  # ชื้นเกินทำให้เชื้อราขึ้น
DAY_START, DAY_END = 6, 18       # เปิดไฟกลางวันจำลอง
FEED_HOUR, WATER_HOUR = 8, 10
PULSE_S = 5                      # เปิดเครื่องให้อาหาร/น้ำกี่วินาที
RELAY_ON, RELAY_OFF = 0, 1

sensor = dht.DHT22(Pin(DHT_PIN))
relay = {name: Pin(p, Pin.OUT, value=RELAY_OFF) for name, p in
         (("heat", RELAY_HEAT), ("fan", RELAY_FAN), ("light", RELAY_LIGHT), ("feed", RELAY_FEED), ("water", RELAY_WATER))}
rtc = RTC()
done_today = {}                  # งานที่ทำแล้ววันนี้ เช่น {"feed": 28}


def pulse(name):
    relay[name].value(RELAY_ON)
    time.sleep(PULSE_S)
    relay[name].value(RELAY_OFF)


def once_a_day(name, hour, h, day):
    if h == hour and done_today.get(name) != day:
        done_today[name] = day
        pulse(name)
        print("ทำงาน %s แล้ว" % name)


while True:
    y, mo, d, wd, h, mi, s, sub = rtc.datetime()
    relay["light"].value(RELAY_ON if DAY_START <= h < DAY_END else RELAY_OFF)
    once_a_day("feed", FEED_HOUR, h, d)
    once_a_day("water", WATER_HOUR, h, d)
    try:
        sensor.measure()
        t, hum = sensor.temperature(), sensor.humidity()
        relay["heat"].value(RELAY_ON if t < TEMP_SET else RELAY_OFF)
        relay["fan"].value(RELAY_ON if (hum > HUMID_HIGH or t > TEMP_HOT) else RELAY_OFF)
        print("temp_c:", t)
        print("humidity:", hum)
    except OSError:
        print("อ่าน DHT22 ไม่ได้")
    time.sleep(2)

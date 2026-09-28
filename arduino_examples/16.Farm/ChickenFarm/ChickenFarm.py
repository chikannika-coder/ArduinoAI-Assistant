# ตัวอย่างเกษตรอัจฉริยะ: ฟาร์มไก่อัจฉริยะ ให้อาหารตามเวลา + คุมอุณหภูมิ (ChickenFarm)
# ต้นฉบับ C++: arduino_examples/16.Farm/ChickenFarm/ChickenFarm.ino  (โครงงาน ทสรช.: ฟาร์มไก่อัจฉริยะ ร.ร.สบเมยวิทยาคม)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: อ่านค่า DHT22 ให้ servo และรีเลย์ทำงาน
# ขา: dht22.SIG=DHT_PIN, servo.SIG=SERVO_PIN, relay.SIG=RELAY_HEAT
# ขาเพิ่ม: RELAY_MIST=out
#
# สิ่งที่แก้จากต้นฉบับ
#   1) ต้นฉบับเช็ก if (hour() == 8) แล้วให้อาหารทุกรอบ loop ตลอดชั่วโมง 8 โมง (ทุก ~6 วินาที = ราว 600 ครั้ง)
#      ตัวอย่างนี้จำว่า "วันนี้ให้มื้อนี้ไปแล้ว" จึงให้แค่มื้อละครั้ง
#   2) ต้นฉบับตั้งเวลาเองด้วย setTime(12,0,0,...) พอไฟดับเวลาจะกลับไปเป็นเที่ยงวันใหม่ทุกครั้ง
#      ตัวอย่างนี้ใช้นาฬิกาในบอร์ด (Thonny ตั้งเวลาให้ตอนเชื่อมต่อ) ถ้าต้องการให้เวลาถูกแม้ไฟดับ ให้ใช้โมดูล RTC DS3231
#   3) เพิ่มช่วงกันสั่นให้ฮีตเตอร์และเครื่องพ่นหมอก
from machine import Pin, PWM, RTC
import dht
import time

DHT_PIN = 27
SERVO_PIN = 18
RELAY_HEAT = 4
RELAY_MIST = 19
FEED_HOURS = (7, 12, 17)        # ให้อาหารตอน 7 โมง เที่ยง และ 5 โมงเย็น
FEED_OPEN_S = 5                  # เปิดช่องอาหารนานกี่วินาที
TEMP_LOW = 20                    # เย็นกว่านี้เปิดไฟกก (ลูกไก่ต้องการอุ่นกว่านี้ ปรับตามอายุไก่)
HUMID_LOW = 60
RELAY_ON, RELAY_OFF = 0, 1

sensor = dht.DHT22(Pin(DHT_PIN))
servo = PWM(Pin(SERVO_PIN), freq=50)
heat = Pin(RELAY_HEAT, Pin.OUT, value=RELAY_OFF)
mist = Pin(RELAY_MIST, Pin.OUT, value=RELAY_OFF)
rtc = RTC()
fed = set()                      # มื้อที่ให้ไปแล้ว เก็บเป็น (วันที่, ชั่วโมง)


def servo_angle(angle):
    servo.duty_u16((500 + angle * 2000 // 180) * 65535 // 20000)


def feed():
    servo_angle(90)              # เปิดช่องปล่อยอาหาร
    time.sleep(FEED_OPEN_S)
    servo_angle(0)


servo_angle(0)
heating = misting = False
while True:
    y, mo, d, wd, h, mi, s, sub = rtc.datetime()
    if h in FEED_HOURS and (d, h) not in fed:
        fed.add((d, h))
        feed()
        print("ให้อาหารมื้อ %d:00 แล้ว" % h)
    if len(fed) > 12:            # ล้างมื้อของวันเก่า ๆ ไม่ให้หน่วยความจำเต็ม
        fed = {x for x in fed if x[0] == d}
    try:
        sensor.measure()
        t, hum = sensor.temperature(), sensor.humidity()
        heating = t < TEMP_LOW or (heating and t < TEMP_LOW + 2)
        misting = hum < HUMID_LOW or (misting and hum < HUMID_LOW + 5)
        heat.value(RELAY_ON if heating else RELAY_OFF)
        mist.value(RELAY_ON if misting else RELAY_OFF)
        print("temp_c:", t)
        print("humidity:", hum)
    except OSError:
        print("อ่าน DHT22 ไม่ได้")
    time.sleep(2)

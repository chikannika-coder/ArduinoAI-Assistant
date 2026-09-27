# ตัวอย่าง Arduino -> MicroPython: วัดระยะด้วยคลื่นเสียง (Ping)
# ต้นฉบับ C++: arduino_examples/06.Sensors/Ping/Ping.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: อ่านระยะทาง ultrasonic
# ขา: hc_sr04.TRIG=TRIG_PIN, hc_sr04.ECHO=ECHO_PIN
# ต้นฉบับใช้เซนเซอร์ Ping))) แบบ 3 ขา ตัวอย่างนี้ใช้ HC-SR04 (4 ขา) ที่มีในห้องเรียนแทน
from machine import Pin, time_pulse_us
import time

TRIG_PIN = 4
ECHO_PIN = 27

trig = Pin(TRIG_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)


def read_distance_cm():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)                  # = delayMicroseconds(10)
    trig.value(0)
    t = time_pulse_us(echo, 1, 30000)  # = pulseIn(echo, HIGH)
    if t < 0:
        return -1                      # ไม่มีเสียงสะท้อนกลับ
    return t * 0.0343 / 2              # เสียงเดินทาง 0.0343 ซม./ไมโครวินาที ไป-กลับ จึงหาร 2


while True:
    d = read_distance_cm()
    print("distance_cm:", round(d, 1))
    time.sleep_ms(100)

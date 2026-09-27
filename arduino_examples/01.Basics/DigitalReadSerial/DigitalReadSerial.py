# ตัวอย่าง Arduino -> MicroPython: อ่านปุ่มแล้วพิมพ์ออกจอ (DigitalReadSerial)
# ต้นฉบับ C++: arduino_examples/01.Basics/DigitalReadSerial/DigitalReadSerial.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: อ่านค่า button
# ขา: button.SIG=BUTTON_PIN
from machine import Pin
import time

BUTTON_PIN = 27
# ต้นฉบับใช้ตัวต้านทาน pull-down ภายนอก ตัวอย่างนี้ใช้ PULL_UP ในชิปแทน จึงไม่ต้องต่อตัวต้านทาน
btn = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

while True:
    pressed = 1 - btn.value()      # กด = 1, ปล่อย = 0
    print("button:", pressed)
    time.sleep_ms(100)

# ตัวอย่าง Arduino -> MicroPython: ไฟกะพริบแบบไม่ใช้ delay (BlinkWithoutDelay)
# ต้นฉบับ C++: arduino_examples/02.Digital/BlinkWithoutDelay/BlinkWithoutDelay.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: ให้ LED บนบอร์ดกระพริบ
# ขา: led.SIG=LED_PIN
from machine import Pin
import time

LED_PIN = 2
INTERVAL_MS = 1000

led = Pin(LED_PIN, Pin.OUT)
previous = time.ticks_ms()             # = unsigned long previousMillis

while True:
    now = time.ticks_ms()              # = millis()
    if time.ticks_diff(now, previous) >= INTERVAL_MS:
        previous = now
        led.value(not led.value())     # สลับ ติด/ดับ
    # ตรงนี้ทำงานอื่นได้เลย เพราะไม่มี sleep มาขวาง

# ตัวอย่าง Arduino -> MicroPython: ไฟวิ่งด้วย for (ForLoopIteration)
# ต้นฉบับ C++: arduino_examples/05.Control/ForLoopIteration/ForLoopIteration.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# ขาเพิ่ม: LED_PINS=out*6@led
from machine import Pin
import time

LED_PINS = [4, 18, 19, 23, 25, 26]      # ต่อ LED 6 ดวง (แต่ละดวงต่อตัวต้านทาน 220Ω)
DELAY_MS = 100

leds = [Pin(p, Pin.OUT) for p in LED_PINS]

while True:
    for led in leds:                    # = for (int i = 2; i < 8; i++)  ไล่จากซ้ายไปขวา
        led.value(1)
        time.sleep_ms(DELAY_MS)
        led.value(0)
    for led in reversed(leds):          # ไล่จากขวากลับมาซ้าย
        led.value(1)
        time.sleep_ms(DELAY_MS)
        led.value(0)

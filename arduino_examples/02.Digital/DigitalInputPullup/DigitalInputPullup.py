# ตัวอย่าง Arduino -> MicroPython: ปุ่มกดแบบ INPUT_PULLUP (DigitalInputPullup)
# ต้นฉบับ C++: arduino_examples/02.Digital/DigitalInputPullup/DigitalInputPullup.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: กดปุ่มให้ LED บนบอร์ดติด
# ขา: button.SIG=BUTTON_PIN, led.SIG=LED_PIN
from machine import Pin
import time

BUTTON_PIN = 27
LED_PIN = 2

btn = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)   # = pinMode(2, INPUT_PULLUP)
led = Pin(LED_PIN, Pin.OUT)

while True:
    value = btn.value()                # ปล่อย = 1, กด = 0 (กลับกันกับ INPUT ธรรมดา)
    print("button:", 1 - value)
    led.value(1 - value)
    time.sleep_ms(50)

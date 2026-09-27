# ตัวอย่าง Arduino -> MicroPython: กดปุ่มไฟติด (Button)
# ต้นฉบับ C++: arduino_examples/02.Digital/Button/Button.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: ถ้ากดปุ่มให้ LED ติด
# ขา: button.SIG=BUTTON_PIN, led.SIG=LED_PIN
from machine import Pin
import time

BUTTON_PIN = 27
LED_PIN = 4

btn = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)   # กด = 0 เพราะใช้ PULL_UP
led = Pin(LED_PIN, Pin.OUT)

while True:
    if btn.value() == 0:
        led.value(1)
    else:
        led.value(0)
    print("button:", 1 - btn.value())
    time.sleep_ms(50)

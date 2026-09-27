# ตัวอย่าง Arduino -> MicroPython: นับจำนวนครั้งที่กดปุ่ม (StateChangeDetection)
# ต้นฉบับ C++: arduino_examples/02.Digital/StateChangeDetection/StateChangeDetection.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: นับจำนวนครั้งที่กดปุ่ม ให้ LED ติด
# ขา: button.SIG=BUTTON_PIN, led.SIG=LED_PIN
from machine import Pin
import time

BUTTON_PIN = 27
LED_PIN = 4

btn = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
led = Pin(LED_PIN, Pin.OUT)

count = 0
last_state = btn.value()

while True:
    state = btn.value()
    if state != last_state:
        if state == 0:                 # เปลี่ยนจากปล่อยเป็นกด
            count += 1
            print("presses:", count)
        time.sleep_ms(50)              # กันปุ่มเด้ง
    last_state = state
    led.value(1 if count % 4 == 0 else 0)   # ติดทุก ๆ 4 ครั้ง
    time.sleep_ms(10)                       # พักสั้น ๆ ให้กดปุ่ม ■ หยุด ได้ทันที

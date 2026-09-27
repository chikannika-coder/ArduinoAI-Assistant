# ตัวอย่าง Arduino -> MicroPython: ไฟกะพริบ (Blink)
# ต้นฉบับ C++: arduino_examples/01.Basics/Blink/Blink.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: ให้ LED บนบอร์ดกระพริบ
# ขา: led.SIG=LED_PIN
from machine import Pin
import time

LED_PIN = 2                 # ขาไฟ LED (โปรแกรมเลือกให้ตามบอร์ด)
led = Pin(LED_PIN, Pin.OUT)  # = pinMode(LED_BUILTIN, OUTPUT)

while True:                  # = void loop()
    led.value(1)             # = digitalWrite(led, HIGH)
    time.sleep(1)            # = delay(1000)
    led.value(0)             # = digitalWrite(led, LOW)
    time.sleep(1)

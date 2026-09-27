# ตัวอย่าง Arduino -> MicroPython: กดปุ่มสลับไฟ (กันปุ่มเด้ง) (Debounce)
# ต้นฉบับ C++: arduino_examples/02.Digital/Debounce/Debounce.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: กดปุ่มสลับ LED
# ขา: button.SIG=BUTTON_PIN, led.SIG=LED_PIN
from machine import Pin
import time

BUTTON_PIN = 27
LED_PIN = 4
DEBOUNCE_MS = 50               # เวลารอให้หน้าสัมผัสปุ่มหยุดสั่น

btn = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
led = Pin(LED_PIN, Pin.OUT)

led_state = 1
button_state = 1               # PULL_UP: ปล่อย = 1
last_reading = 1
last_change = time.ticks_ms()
led.value(led_state)

while True:
    reading = btn.value()
    if reading != last_reading:
        last_change = time.ticks_ms()
    if time.ticks_diff(time.ticks_ms(), last_change) > DEBOUNCE_MS:
        if reading != button_state:
            button_state = reading
            if button_state == 0:          # เพิ่งกด
                led_state = 1 - led_state
                print("led:", led_state)
    led.value(led_state)
    last_reading = reading
    time.sleep_ms(1)

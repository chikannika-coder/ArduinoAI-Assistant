# ตัวอย่าง Arduino -> MicroPython: นาฬิกาทรายดิจิทัล (p08_DigitalHourglass)
# ต้นฉบับ C++: arduino_examples/10.StarterKit/p08_DigitalHourglass/p08_DigitalHourglass.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: อ่านค่า button
# ขา: button.SIG=SWITCH_PIN
# ขาเพิ่ม: LED_PINS=out*6
# ต้นฉบับใช้สวิตช์เอียง (tilt switch) ต่อแบบเดียวกับปุ่มกด
from machine import Pin
import time

SWITCH_PIN = 27
LED_PINS = [4, 18, 19, 23, 25, 26]
INTERVAL_MS = 10000     # ต้นฉบับ 600000 (10 นาที) ลดเหลือ 10 วินาทีให้เห็นผลในห้องเรียน

switch = Pin(SWITCH_PIN, Pin.IN, Pin.PULL_UP)
leds = [Pin(p, Pin.OUT) for p in LED_PINS]

previous = time.ticks_ms()
next_led = 0
prev_state = switch.value()

while True:
    now = time.ticks_ms()
    if time.ticks_diff(now, previous) > INTERVAL_MS and next_led < len(leds):
        previous = now
        leds[next_led].value(1)
        next_led += 1
        print("leds_on:", next_led)
    state = switch.value()
    if state != prev_state:           # เอียงนาฬิกา = เริ่มนับใหม่
        for led in leds:
            led.value(0)
        next_led = 0
        previous = now
        print("leds_on:", 0)
    prev_state = state
    time.sleep_ms(20)

# ตัวอย่าง Arduino -> MicroPython: ไฟค่อย ๆ สว่าง-หรี่ (Fade)
# ต้นฉบับ C++: arduino_examples/01.Basics/Fade/Fade.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: ทดสอบ led
# ขา: led.SIG=LED_PIN
from machine import Pin, PWM
import time

LED_PIN = 4
led = PWM(Pin(LED_PIN), freq=1000)   # = analogWrite ต้องใช้ PWM

brightness = 0
fade_amount = 5

while True:
    led.duty_u16(brightness * 257)   # = analogWrite(led, brightness)  (0-255 -> 0-65535)
    brightness = brightness + fade_amount
    if brightness <= 0 or brightness >= 255:
        fade_amount = -fade_amount
    print("brightness:", brightness)
    time.sleep_ms(30)

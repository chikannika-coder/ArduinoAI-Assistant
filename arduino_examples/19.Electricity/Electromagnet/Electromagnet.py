# พื้นฐานไฟฟ้า: ปั้นจั่นแม่เหล็กไฟฟ้า เปิด-ปิดด้วยปุ่ม (Electromagnet)
# ต้นฉบับ C++: arduino_examples/19.Electricity/Electromagnet/Electromagnet.ino  (เขียนเพิ่มในเวอร์ชัน 2.7)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: กดปุ่ม ให้รีเลย์ทำงาน
# ขา: button.SIG=BUTTON_PIN, relay.SIG=RELAY_PIN
#
# แม่เหล็กไฟฟ้า: พันลวดทองแดงเคลือบ 50-100 รอบรอบตะปูเหล็ก ต่อกับถ่าน 1.5-3V ผ่านหน้าสัมผัสรีเลย์
# กดปุ่ม 1 ครั้ง = ดูด (หยิบคลิปหนีบกระดาษ) กดอีกครั้ง = ปล่อย
# ทดลองอย่างยุติธรรม (fair test): เปลี่ยนทีละอย่าง จำนวนรอบ / จำนวนถ่าน / ขนาดตะปู แล้วนับคลิปที่ดูดได้
# ⚠ ขดลวดกินกระแสสูงและร้อนได้ อย่าเปิดค้างนาน โปรแกรมปิดให้เองเมื่อครบ MAX_ON_S
#   ห้ามต่อขดลวดเข้าขาบอร์ดตรง ๆ ต้องผ่านรีเลย์ หรือทรานซิสเตอร์ + ไดโอดกันไฟย้อน (เหมือนมอเตอร์ของหุ่นบีม)
from machine import Pin
import time

BUTTON_PIN = 27
RELAY_PIN = 4
MAX_ON_S = 20
RELAY_ON, RELAY_OFF = 0, 1

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
coil = Pin(RELAY_PIN, Pin.OUT, value=RELAY_OFF)
magnet = False
on_since = 0
was_pressed = False
while True:
    pressed = button.value() == 0
    if pressed and not was_pressed:                 # กดครั้งใหม่ (ไม่นับการกดค้าง)
        magnet = not magnet
        on_since = time.ticks_ms()
        print("แม่เหล็กทำงาน" if magnet else "ปล่อยของแล้ว")
    was_pressed = pressed
    if magnet and time.ticks_diff(time.ticks_ms(), on_since) > MAX_ON_S * 1000:
        magnet = False
        print("เปิดนานเกินไป ปิดให้เพื่อไม่ให้ขดลวดร้อน")
    coil.value(RELAY_ON if magnet else RELAY_OFF)
    print("magnet:", 1 if magnet else 0)
    time.sleep_ms(30)

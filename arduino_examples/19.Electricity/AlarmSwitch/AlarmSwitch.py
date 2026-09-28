# พื้นฐานไฟฟ้า: สัญญาณกันขโมยและเตือนฝนตก (AlarmSwitch)
# ต้นฉบับ C++: arduino_examples/19.Electricity/AlarmSwitch/AlarmSwitch.ino  (เขียนเพิ่มในเวอร์ชัน 2.7)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: กดปุ่ม ให้ buzzer ดัง และ LED ติด
# ขา: button.SIG=RESET_PIN, buzzer.SIG=BUZZER_PIN, led.SIG=LED_PIN
# ขาเพิ่ม: TRAP_PIN=inpu, RAIN_PIN=inpu
#
# สวิตช์เตือนภัยทำเองได้ 2 แบบ
#   กันขโมย (TRAP_PIN): ลวดเส้นเล็กพันใต้กล่องของมีค่า ต่อจาก TRAP_PIN ลง GND ปกติวงจรครบ (อ่านได้ 0)
#                       ถ้ายกกล่อง ลวดหลุด วงจรขาด (อ่านได้ 1) -> เตือน
#   เตือนฝน (RAIN_PIN): ไม้หนีบผ้าติดหมุดโลหะ 2 ตัว คั่นด้วยกระดาษทิชชู ต่อหมุดหนึ่งเข้า RAIN_PIN อีกหมุดลง GND
#                       ฝนตก กระดาษเปียกยุ่ย หมุดแตะกัน วงจรครบ (อ่านได้ 0) -> เตือน
# สัญญาณเตือนจะค้างไว้จนกว่าจะกดปุ่ม RESET (เหมือนสัญญาณกันขโมยจริง) ไฟกะพริบด้วย ผู้ที่ไม่ได้ยินเสียงก็เห็น
from machine import Pin
import time

TRAP_PIN = 33
RAIN_PIN = 32
RESET_PIN = 27
BUZZER_PIN = 18
LED_PIN = 4

trap = Pin(TRAP_PIN, Pin.IN, Pin.PULL_UP)
rain = Pin(RAIN_PIN, Pin.IN, Pin.PULL_UP)
reset = Pin(RESET_PIN, Pin.IN, Pin.PULL_UP)
buzzer = Pin(BUZZER_PIN, Pin.OUT)
led = Pin(LED_PIN, Pin.OUT)
alarm = ""
n = 0
while True:
    if not alarm and trap.value() == 1:
        alarm = "มีคนยกกล่อง!"
    if not alarm and rain.value() == 0:
        alarm = "ฝนตก! เก็บผ้า"
    if alarm and reset.value() == 0:
        alarm = ""
        print("รีเซ็ตแล้ว")
    n += 1
    blink = alarm and n % 10 < 5
    buzzer.value(1 if blink else 0)
    led.value(1 if blink else 0)
    if alarm and n % 50 == 0:
        print(alarm)
    print("alarm:", 1 if alarm else 0)
    time.sleep_ms(50)

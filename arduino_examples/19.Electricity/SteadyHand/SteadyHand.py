# พื้นฐานไฟฟ้า: เกมมือนิ่ง (ห่วงลวดห้ามแตะรางลวด) (SteadyHand)
# ต้นฉบับ C++: arduino_examples/19.Electricity/SteadyHand/SteadyHand.ino  (เขียนเพิ่มในเวอร์ชัน 2.7)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: กดปุ่ม ให้ buzzer ดัง
# ขา: button.SIG=TRACK_PIN, buzzer.SIG=BUZZER_PIN
# ขาเพิ่ม: FINISH_PIN=inpu
#
# เกมนี้คือ "สวิตช์พิเศษ": รางลวดดัดโค้งกับห่วงลวดที่ถือ ถ้าห่วงแตะราง วงจรครบ = สวิตช์ปิด
# ต่อสาย: รางลวด -> ขา TRACK_PIN, ห่วงลวด -> GND, แผ่นโลหะปลายทาง -> ขา FINISH_PIN
# (ภาพการต่อสายแสดงรางลวดเป็นปุ่มกด เพราะทำงานเหมือนปุ่มที่ต่อลง GND)
# บอร์ดนับจำนวนครั้งที่แตะ และจับเวลาจนห่วงแตะแผ่นปลายทาง
from machine import Pin
import time

TRACK_PIN = 27
FINISH_PIN = 26
BUZZER_PIN = 18

track = Pin(TRACK_PIN, Pin.IN, Pin.PULL_UP)       # แตะ = 0
finish = Pin(FINISH_PIN, Pin.IN, Pin.PULL_UP)
buzzer = Pin(BUZZER_PIN, Pin.OUT)
touches = 0
start = time.ticks_ms()
touching = False
while True:
    if track.value() == 0:
        buzzer.value(1)
        if not touching:                            # นับตอนเริ่มแตะเท่านั้น ไม่นับซ้ำระหว่างที่ยังแตะอยู่
            touches += 1
            touching = True
    else:
        buzzer.value(0)
        touching = False
    if finish.value() == 0:
        secs = time.ticks_diff(time.ticks_ms(), start) / 1000
        print("ถึงปลายทาง! เวลา %.1f วินาที แตะราง %d ครั้ง" % (secs, touches))
        for _ in range(3):
            buzzer.value(1)
            time.sleep_ms(100)
            buzzer.value(0)
            time.sleep_ms(100)
        time.sleep(3)
        touches, start = 0, time.ticks_ms()        # เริ่มรอบใหม่
    print("touches:", touches)
    time.sleep_ms(20)

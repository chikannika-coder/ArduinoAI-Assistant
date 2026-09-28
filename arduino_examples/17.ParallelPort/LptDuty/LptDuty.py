# จาก Turbo C พอร์ตขนาน สู่ MicroPython: ปรับความสว่าง/ความเร็วด้วย duty (LptDuty)
# ต้นฉบับ Turbo C: arduino_examples/17.ParallelPort/LptDuty/LptDuty.c  (testoutport2_duty.c ของครู)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: ปรับไฟ LED และกดปุ่ม
# ขา: led.SIG=D0_PIN, button.SIG=UP_BTN
# ขาเพิ่ม: DOWN_BTN=inpu
#
# ของเดิมทำ PWM ด้วยมือ: เปิด duty มิลลิวินาที ปิด (100 - duty) มิลลิวินาที วนไปเรื่อย ๆ กดแป้น + / - เพื่อปรับ
# MicroPython มีตัวสร้าง PWM ในชิป (ฮาร์ดแวร์) ทำงานเองเบื้องหลัง เร็วกว่ามาก ไฟไม่กะพริบ และโปรแกรมทำอย่างอื่นต่อได้
#   Turbo C                                     MicroPython
#   outport(0x378,1); delay(duty);              pwm.duty_u16(duty * 65535 // 100)   (สั่งครั้งเดียว ชิปทำเอง)
#   outport(0x378,0); delay(100-duty);
#   getch() == '+' / '-'                        ปุ่ม UP_BTN / DOWN_BTN
from machine import Pin, PWM
import time

D0_PIN = 4
UP_BTN = 27
DOWN_BTN = 26

pwm = PWM(Pin(D0_PIN), freq=1000)       # 1000 ครั้งต่อวินาที (ของเดิมได้แค่ 10 ครั้งต่อวินาที จึงเห็นไฟกะพริบ)
up = Pin(UP_BTN, Pin.IN, Pin.PULL_UP)
down = Pin(DOWN_BTN, Pin.IN, Pin.PULL_UP)
duty = 0                                 # 0 ~ 100 เหมือนของเดิม

while True:
    if up.value() == 0:
        duty = min(100, duty + 1)
    if down.value() == 0:
        duty = max(0, duty - 1)
    pwm.duty_u16(duty * 65535 // 100)
    print("duty:", duty)
    time.sleep_ms(50)

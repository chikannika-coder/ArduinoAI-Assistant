# จาก Turbo C พอร์ตขนาน สู่ MicroPython: เซนเซอร์สั่งมอเตอร์ (LptSensorMotor)
# ต้นฉบับ Turbo C: arduino_examples/17.ParallelPort/LptSensorMotor/LptSensorMotor.c  (IR_M.C และ LDR_M.C ของครู)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: ถ้าเจอวัตถุ ir ให้ LED ติด
# ขา: ir_obstacle.SIG=S4_PIN, led.SIG=D0_PIN
#
# เทียบกับของเดิม
#   indata = inport(0x379);              s4 = sensor.value()        ขา S4 (ขา 13 ของพอร์ตขนาน) -> ขาบอร์ด S4_PIN
#   if ((indata & 0x10) == 0x10)         if s4 == 1:                 0x10 = 16 = บิตที่ 4 คือขา S4
#       outport(0x378, 0);                   d0.value(0)
#   else outport(0x378, 1);              else: d0.value(1)
# ไฟล์ LDR_M.C ของครูเหมือนกันทุกอย่าง แค่สลับเปิด/ปิด ให้แก้ LDR_MODE = True
# ภาพการต่อสายใช้ LED แทนมอเตอร์ ถ้าต่อมอเตอร์ต้องผ่านทรานซิสเตอร์หรือรีเลย์
from machine import Pin
import time

S4_PIN = 27
D0_PIN = 4
LDR_MODE = False             # False = IR_M.C (เจอวัตถุแล้วหมุน), True = LDR_M.C (กลับด้าน)

sensor = Pin(S4_PIN, Pin.IN, Pin.PULL_UP)
d0 = Pin(D0_PIN, Pin.OUT)

while True:
    s4 = sensor.value()                    # ของเดิม: (indata & 0x10) == 0x10
    on = (s4 == 1) if LDR_MODE else (s4 == 0)
    d0.value(1 if on else 0)
    print("s4:", s4)
    time.sleep_ms(50)

# ตัวอย่าง Arduino -> MicroPython: สเต็ปเปอร์หมุนครบรอบ (stepper_oneRevolution)
# ต้นฉบับ C++: arduino_examples/13.Stepper/stepper_oneRevolution/stepper_oneRevolution.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: หมุน stepper
# ขา: stepper.A=IN1_PIN, stepper.B=IN2_PIN, stepper.C=IN3_PIN, stepper.D=IN4_PIN
# ใช้มอเตอร์ 28BYJ-48 กับบอร์ดขับ ULN2003 (ต้นฉบับใช้สเต็ปเปอร์ 200 ขั้น/รอบ)
from machine import Pin
import time

IN1_PIN = 4
IN2_PIN = 18
IN3_PIN = 19
IN4_PIN = 23
STEPS_PER_REV = 4096            # 28BYJ-48 แบบ half-step

coils = [Pin(p, Pin.OUT) for p in (IN1_PIN, IN2_PIN, IN3_PIN, IN4_PIN)]
SEQ = [[1, 0, 0, 0], [1, 1, 0, 0], [0, 1, 0, 0], [0, 1, 1, 0],
       [0, 0, 1, 0], [0, 0, 1, 1], [0, 0, 0, 1], [1, 0, 0, 1]]


def step(n):
    """= myStepper.step(n)  ค่าบวกหมุนตามเข็ม ค่าลบทวนเข็ม"""
    direction = 1 if n > 0 else -1
    for i in range(abs(n)):
        pattern = SEQ[(i * direction) % 8]
        for coil, v in zip(coils, pattern):
            coil.value(v)
        time.sleep_ms(1)
    for coil in coils:
        coil.value(0)                # ปล่อยขดลวด มอเตอร์จะได้ไม่ร้อน


while True:
    print("direction:", 1)
    step(STEPS_PER_REV)
    time.sleep_ms(500)
    print("direction:", -1)
    step(-STEPS_PER_REV)
    time.sleep_ms(500)

# ตัวอย่าง Arduino -> MicroPython: เซอร์โวกวาดไปมา (Sweep)
# ต้นฉบับ C++: arduino_examples/11.Servo/Sweep/Sweep.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: หมุน servo
# ขา: servo.SIG=SERVO_PIN
from machine import Pin, PWM
import time

SERVO_PIN = 18
servo = PWM(Pin(SERVO_PIN), freq=50)      # = myservo.attach(9)


def servo_angle(angle):
    us = 500 + angle * 2000 // 180
    servo.duty_u16(us * 65535 // 20000)


while True:
    for pos in range(0, 181):             # 0 -> 180 องศา
        servo_angle(pos)                  # = myservo.write(pos)
        time.sleep_ms(15)
    print("angle:", 180)
    for pos in range(180, -1, -1):        # 180 -> 0 องศา
        servo_angle(pos)
        time.sleep_ms(15)
    print("angle:", 0)

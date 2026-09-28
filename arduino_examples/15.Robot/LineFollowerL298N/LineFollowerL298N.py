# ตัวอย่าง: หุ่นยนต์เดินตามเส้นด้วยโมดูล TCRT5000 2 ตัว + ไดรเวอร์ L298N (LineFollowerL298N)
# ต้นฉบับ C++: arduino_examples/15.Robot/LineFollowerL298N/LineFollowerL298N.ino  (เขียนเพิ่มในเวอร์ชัน 2.4)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: ถ้าเจอเส้น TCRT5000 ให้มอเตอร์ L298N หมุน
# ขา: line_tcrt5000.SIG=LEFT_SENSOR, motor_l298n.IN1=IN1, motor_l298n.IN2=IN2, motor_l298n.ENA=ENA
# ขาเพิ่ม: RIGHT_SENSOR=inp, IN3=out, IN4=out, ENB=pwm
#
# ทางเลือกของหุ่นบีม ถ้าโรงเรียนมีโมดูล TCRT5000 และ L298N (ภาพการต่อสายแสดงเซนเซอร์ซ้ายและมอเตอร์ซ้าย)
#   เซนเซอร์ขวาต่อแบบเดียวกันที่ขา RIGHT_SENSOR, มอเตอร์ขวาต่อที่ OUT3/OUT4 ของ L298N คุมด้วย IN3 IN4 ENB
#   ถอดจัมเปอร์ที่ขา ENA และ ENB ของ L298N ออกก่อนต่อสาย
#   L298N กินแรงดันไปราว 2V ถ่าน 4.5V ของหุ่นบีมจึงอาจแรงไม่พอ แนะนำถ่าน 6-9V ต่อที่ขา 12V ของ L298N และต่อ GND ร่วมกับบอร์ด
from machine import Pin, PWM
import time

LEFT_SENSOR = 32             # ขา DO ของ TCRT5000 ซ้าย
RIGHT_SENSOR = 33            # ขา DO ของ TCRT5000 ขวา
IN1 = 25                     # มอเตอร์ซ้าย: IN1 IN2 กำหนดทิศ ENA กำหนดความเร็ว
IN2 = 26
ENA = 27
IN3 = 14                     # มอเตอร์ขวา: IN3 IN4 กำหนดทิศ ENB กำหนดความเร็ว
IN4 = 12
ENB = 13
SPEED = 60                   # ความเร็ว 0-100 %
BLACK = 1                    # โมดูลส่วนใหญ่ให้ค่า 1 เมื่ออยู่บนเส้นดำ ถ้าของจริงกลับกัน ให้เปลี่ยนเป็น 0

left_sensor = Pin(LEFT_SENSOR, Pin.IN)
right_sensor = Pin(RIGHT_SENSOR, Pin.IN)
motors = [(Pin(IN1, Pin.OUT), Pin(IN2, Pin.OUT), PWM(Pin(ENA), freq=1000)),
          (Pin(IN3, Pin.OUT), Pin(IN4, Pin.OUT), PWM(Pin(ENB), freq=1000))]


def drive(left, right):
    """ความเร็วล้อซ้าย/ขวา -100 ถึง 100 (ค่าลบ = ถอยหลัง)"""
    for (a, b, en), speed in zip(motors, (left, right)):
        a.value(1 if speed > 0 else 0)
        b.value(1 if speed < 0 else 0)
        en.duty_u16(min(abs(speed), 100) * 65535 // 100)


drive(0, 0)
n = 0
while True:
    left_black = left_sensor.value() == BLACK
    right_black = right_sensor.value() == BLACK
    if not left_black and not right_black:
        drive(SPEED, SPEED)          # อยู่คร่อมเส้น: วิ่งตรง
    elif left_black and not right_black:
        drive(0, SPEED)              # ซ้ายตกเส้นดำ: เลี้ยวซ้าย
    elif right_black and not left_black:
        drive(SPEED, 0)              # ขวาตกเส้นดำ: เลี้ยวขวา
    else:
        drive(0, 0)                  # เห็นเส้นดำทั้งสองข้าง (เส้นชัย/ทางแยก): หยุด
    n += 1
    if n % 10 == 0:
        print("left_black:", int(left_black))
        print("right_black:", int(right_black))
    time.sleep_ms(20)

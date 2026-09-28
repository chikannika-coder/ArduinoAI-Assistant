# ตัวอย่างต่อยอดหุ่นยนต์บีม: หุ่นยนต์เดินตามเส้นที่เขียนโปรแกรมได้ (BeamLineFollower)
# ต้นฉบับ C++: arduino_examples/15.Robot/BeamLineFollower/BeamLineFollower.ino  (เขียนเพิ่มในเวอร์ชัน 2.4)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: ถ้าเซนเซอร์หุ่นบีมมากกว่า 50 ให้มอเตอร์หุ่นบีมหมุน
# ขา: beam_ir.SIG=LEFT_SENSOR, beam_motor.SIG=LEFT_MOTOR
# ขาเพิ่ม: RIGHT_SENSOR=adc, RIGHT_MOTOR=pwm
#
# ใช้วงจรหุ่นยนต์บีมเดิมเกือบทั้งหมด เปลี่ยนแค่ "สมอง" จากเซนเซอร์ต่อตรงเข้าทรานซิสเตอร์ เป็นบอร์ดที่เขียนโปรแกรมได้
# ถอดถ่านออกก่อน แล้วทำทีละข้าง (ภาพการต่อสายแสดงข้างซ้าย ข้างขวาต่อแบบเดียวกัน):
#   1) ถอดสายขาวของเซนเซอร์ออกจากแถว 10 และย้ายสายตัวต้านทานปรับค่าได้ที่อยู่ในแถว 10 ไปแถวว่าง (เช่น แถว 5)
#      เสียบสายขาวไว้แถวเดียวกัน แล้วต่อสายจากแถวนั้นไปขา LEFT_SENSOR / RIGHT_SENSOR
#   2) ย้ายสายเขียว (+) ของแผงเซนเซอร์ไปที่ 3V3 ของบอร์ด (ห้ามใช้ไฟถ่าน 4.5V)
#   3) ต่อสายจากขา LEFT_MOTOR / RIGHT_MOTOR เข้าแถว 10 (สัญญาณจะผ่านตัวต้านทาน 1k เดิมไปขา B ของ BC337)
#   4) ต่อ GND ของบอร์ดเข้ารางไฟลบของบอร์ดทดลอง แล้วใส่ถ่านกลับ
# มอเตอร์ยังใช้ไฟจากถ่าน 4.5V ผ่าน BC337 + BD679 เหมือนเดิม ห้ามต่อมอเตอร์เข้าขาบอร์ดโดยตรง
from machine import Pin, ADC, PWM
import time

LEFT_SENSOR = 34             # สายขาวของเซนเซอร์ซ้าย
RIGHT_SENSOR = 35            # สายขาวของเซนเซอร์ขวา
LEFT_MOTOR = 18              # แถว 10 ของวงจรล้อซ้าย
RIGHT_MOTOR = 19             # แถว 10 ของวงจรล้อขวา
THRESHOLD = 500              # มากกว่านี้ = พื้นขาว, น้อยกว่า = เส้นดำ (หาค่าด้วยตัวอย่าง BeamSensorRead)
SPEED = 70                   # ความเร็วมอเตอร์ 0-100 %


def make_adc(pin):
    """สร้างตัวอ่านแอนะล็อกให้ใช้ได้ทุกบอร์ด"""
    if pin == "A0":              # ESP8266 มีขาแอนะล็อกขาเดียว
        return ADC(0)
    adc = ADC(Pin(pin))
    if hasattr(adc, "atten"):    # ESP32: ให้อ่านได้ช่วง 0-3.3V
        adc.atten(ADC.ATTN_11DB)
    return adc


def analog_read(adc):
    """อ่านค่า 0-1023 เหมือน analogRead() ของ Arduino"""
    return adc.read_u16() >> 6


def set_motor(motor, percent):
    """ความเร็ว 0-100 % (PWM เปิด-ปิดไฟเร็ว ๆ ยิ่งเปิดนาน มอเตอร์ยิ่งเร็ว)"""
    motor.duty_u16(percent * 65535 // 100)


left_adc = make_adc(LEFT_SENSOR)
right_adc = make_adc(RIGHT_SENSOR)
left_motor = PWM(Pin(LEFT_MOTOR), freq=1000)
right_motor = PWM(Pin(RIGHT_MOTOR), freq=1000)
set_motor(left_motor, 0)
set_motor(right_motor, 0)

n = 0
while True:
    left = analog_read(left_adc)
    right = analog_read(right_adc)
    # กฎเดียวกับหุ่นยนต์บีม: เซนเซอร์เห็นพื้นขาว ล้อข้างนั้นหมุน / เห็นเส้นดำ ล้อข้างนั้นหยุด
    # เซนเซอร์ซ้ายตกเส้นดำ -> ล้อซ้ายหยุด ล้อขวาหมุน -> รถเลี้ยวซ้ายกลับเข้าเส้น (ขวาก็กลับกัน)
    set_motor(left_motor, SPEED if left > THRESHOLD else 0)
    set_motor(right_motor, SPEED if right > THRESHOLD else 0)
    n += 1
    if n % 10 == 0:          # ส่งค่าไปทำกราฟทุก 0.2 วินาที ไม่ให้ข้อความถี่เกินไป
        print("left:", left)
        print("right:", right)
    time.sleep_ms(20)

# ลองต่อยอด:
#   1) ถ้าเซนเซอร์ทั้งสองเห็นเส้นดำ (ทางแยก) ให้วิ่งตรงต่อแทนการหยุด
#   2) ตอนเลี้ยว ให้ล้อด้านในหมุนช้าลง (เช่น 30 %) แทนการหยุด รถจะเลี้ยวนุ่มขึ้น
#   3) จำว่าหลุดเส้นไปทางไหนล่าสุด ถ้าหลุดเส้นทั้งสองข้าง ให้หมุนกลับหาเส้นทางนั้น

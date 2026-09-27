# ตัวอย่าง Arduino -> MicroPython: เข็มบอกอารมณ์ (p05_ServoMoodIndicator)
# ต้นฉบับ C++: arduino_examples/10.StarterKit/p05_ServoMoodIndicator/p05_ServoMoodIndicator.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: หมุน servo ตาม potentiometer
# ขา: potentiometer.SIG=POT_PIN, servo.SIG=SERVO_PIN
from machine import Pin, ADC, PWM
import time

POT_PIN = 34
SERVO_PIN = 18

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


def map_range(x, in_min, in_max, out_min, out_max):
    """เหมือน map() ของ Arduino"""
    if in_max == in_min:
        return out_min
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

pot = make_adc(POT_PIN)
servo = PWM(Pin(SERVO_PIN), freq=50)


def servo_angle(angle):
    """= myServo.write(angle)  พัลส์ 0.5-2.5 ms ทุก 20 ms"""
    angle = max(0, min(180, angle))
    us = 500 + angle * 2000 // 180
    servo.duty_u16(us * 65535 // 20000)


while True:
    pot_val = analog_read(pot)
    angle = map_range(pot_val, 0, 1023, 0, 179)
    print("pot:", pot_val)
    print("angle:", angle)
    servo_angle(angle)
    time.sleep_ms(15)

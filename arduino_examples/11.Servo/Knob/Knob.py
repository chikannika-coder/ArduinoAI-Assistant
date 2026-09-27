# ตัวอย่าง Arduino -> MicroPython: หมุนเซอร์โวด้วยปุ่มหมุน (Knob)
# ต้นฉบับ C++: arduino_examples/11.Servo/Knob/Knob.ino  (Arduino IDE 1.6.0)
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
    us = 500 + angle * 2000 // 180
    servo.duty_u16(us * 65535 // 20000)


while True:
    val = map_range(analog_read(pot), 0, 1023, 0, 180)
    servo_angle(val)
    print("angle:", val)
    time.sleep_ms(15)

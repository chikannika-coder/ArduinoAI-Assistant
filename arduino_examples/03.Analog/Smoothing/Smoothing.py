# ตัวอย่าง Arduino -> MicroPython: ทำค่าเซนเซอร์ให้นิ่ง (Smoothing)
# ต้นฉบับ C++: arduino_examples/03.Analog/Smoothing/Smoothing.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: อ่านค่า potentiometer
# ขา: potentiometer.SIG=POT_PIN
from machine import Pin, ADC
import time

POT_PIN = 34
NUM_READINGS = 10

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

readings = [0] * NUM_READINGS          # = int readings[numReadings]
index = 0
total = 0

while True:
    total -= readings[index]
    readings[index] = analog_read(pot)
    total += readings[index]
    index = (index + 1) % NUM_READINGS
    average = total // NUM_READINGS
    print("raw:", readings[index - 1])
    print("average:", average)
    time.sleep_ms(20)

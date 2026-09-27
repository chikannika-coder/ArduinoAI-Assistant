# ตัวอย่าง Arduino -> MicroPython: เลือกทำตามช่วงค่า (switch) (switchCase)
# ต้นฉบับ C++: arduino_examples/05.Control/switchCase/switchCase.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: อ่านค่าแสง ldr
# ขา: ldr.SIG=SENSOR_PIN
from machine import Pin, ADC
import time

SENSOR_PIN = 34
SENSOR_MIN = 0
SENSOR_MAX = 600       # ปรับตามค่าที่อ่านได้จริงในห้อง

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

sensor = make_adc(SENSOR_PIN)
NAMES = {0: "มืด (dark)", 1: "สลัว (dim)", 2: "ปานกลาง (medium)", 3: "สว่าง (bright)"}

while True:
    reading = analog_read(sensor)
    level = max(0, min(map_range(reading, SENSOR_MIN, SENSOR_MAX, 0, 3), 3))
    # Python ไม่มี switch/case ใช้ if/elif หรือ dict แทน
    print("light:", reading)
    print(NAMES[level])
    time.sleep_ms(300)

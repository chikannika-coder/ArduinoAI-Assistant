# ตัวอย่าง Arduino -> MicroPython: ถ้า...แล้ว (if) (IfStatementConditional)
# ต้นฉบับ C++: arduino_examples/05.Control/IfStatementConditional/IfStatementConditional.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: ถ้า potentiometer มากกว่า 40 ให้ LED ติด
# ขา: potentiometer.SIG=POT_PIN, led.SIG=LED_PIN
from machine import Pin, ADC
import time

POT_PIN = 34
LED_PIN = 4
THRESHOLD = 400                        # ค่า 0-1023

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
led = Pin(LED_PIN, Pin.OUT)

while True:
    value = analog_read(pot)
    if value > THRESHOLD:
        led.value(1)
    else:
        led.value(0)
    print("value:", value)
    time.sleep_ms(50)

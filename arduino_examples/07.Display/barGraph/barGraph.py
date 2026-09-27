# ตัวอย่าง Arduino -> MicroPython: แถบไฟแสดงระดับ (barGraph)
# ต้นฉบับ C++: arduino_examples/07.Display/barGraph/barGraph.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: อ่านค่า potentiometer
# ขา: potentiometer.SIG=POT_PIN
# ขาเพิ่ม: LED_PINS=out*8
from machine import Pin, ADC
import time

POT_PIN = 34
LED_PINS = [4, 18, 19, 23, 25, 26, 27, 13]   # LED 8 ดวง (ต้นฉบับใช้ 10 ดวง)

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
leds = [Pin(p, Pin.OUT) for p in LED_PINS]

while True:
    reading = analog_read(pot)
    level = map_range(reading, 0, 1023, 0, len(leds))
    for i, led in enumerate(leds):
        led.value(1 if i < level else 0)
    print("level:", level)
    time.sleep_ms(50)

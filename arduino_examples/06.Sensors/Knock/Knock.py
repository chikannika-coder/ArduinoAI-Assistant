# ตัวอย่าง Arduino -> MicroPython: ตรวจจับการเคาะ (Knock)
# ต้นฉบับ C++: arduino_examples/06.Sensors/Knock/Knock.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: ถ้าเซนเซอร์เสียงดังให้ LED ติด
# ขา: sound.SIG=SENSOR_PIN, led.SIG=LED_PIN
# ต้นฉบับใช้แผ่นเพียโซเป็นเซนเซอร์เคาะ ตัวอย่างนี้ใช้โมดูลเซนเซอร์เสียง (KY-038) ขา AO แทน
from machine import Pin, ADC
import time

SENSOR_PIN = 34
LED_PIN = 4
THRESHOLD = 100                        # ค่า 0-1023 ปรับตามความไวของเซนเซอร์

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
led = Pin(LED_PIN, Pin.OUT)
state = 0

while True:
    reading = analog_read(sensor)
    print("sound:", reading)
    if reading >= THRESHOLD:
        state = 1 - state              # = ledState = !ledState
        led.value(state)
        print("knock: 1")
    time.sleep_ms(100)

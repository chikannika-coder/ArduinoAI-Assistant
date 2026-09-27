# ตัวอย่าง Arduino -> MicroPython: ปรับเทียบเซนเซอร์ (Calibration)
# ต้นฉบับ C++: arduino_examples/03.Analog/Calibration/Calibration.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: อ่านค่า ldr ควบคุม led
# ขา: ldr.SIG=SENSOR_PIN, led.SIG=LED_PIN
from machine import Pin, ADC, PWM
import time

SENSOR_PIN = 34
LED_PIN = 4

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
led = PWM(Pin(LED_PIN), freq=1000)

# ---- 5 วินาทีแรก: ปรับเทียบ (ส่องไฟ / บังแสง ให้เซนเซอร์เห็นค่าต่ำสุดและสูงสุด)
print("calibrating: 1")
led.duty_u16(65535)                            # ไฟติดเต็ม = กำลังปรับเทียบ
low, high = 1023, 0
start = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), start) < 5000:
    v = analog_read(sensor)
    low = min(low, v)
    high = max(high, v)
led.duty_u16(0)
print("sensor_min:", low)
print("sensor_max:", high)

while True:
    v = analog_read(sensor)
    level = map_range(v, low, high, 0, 255)
    level = max(0, min(level, 255))            # = constrain(level, 0, 255)
    led.duty_u16(level * 257)
    print("level:", level)
    time.sleep_ms(50)

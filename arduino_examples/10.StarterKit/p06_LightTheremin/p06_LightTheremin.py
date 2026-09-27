# ตัวอย่าง Arduino -> MicroPython: เครื่องดนตรีแสง (เทอร์มิน) (p06_LightTheremin)
# ต้นฉบับ C++: arduino_examples/10.StarterKit/p06_LightTheremin/p06_LightTheremin.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: อ่านค่าแสง ldr เล่นโน้ต passive buzzer
# ขา: ldr.SIG=SENSOR_PIN, buzzer_passive.SIG=BUZZER_PIN
from machine import Pin, ADC, PWM
import time

SENSOR_PIN = 34
BUZZER_PIN = 18

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
bz = PWM(Pin(BUZZER_PIN))
bz.duty_u16(0)

# ---- 5 วินาทีแรก: โบกมือเหนือเซนเซอร์ให้เห็นค่ามืดสุด/สว่างสุด
print("calibrating: 1")
low, high = 1023, 0
start = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), start) < 5000:
    v = analog_read(sensor)
    low, high = min(low, v), max(high, v)
print("calibrating: 0")

while True:
    v = analog_read(sensor)
    pitch = max(50, map_range(v, low, high, 50, 4000))
    bz.freq(pitch)                    # = tone(8, pitch, 20)
    bz.duty_u16(32768)
    print("pitch:", pitch)
    time.sleep_ms(20)

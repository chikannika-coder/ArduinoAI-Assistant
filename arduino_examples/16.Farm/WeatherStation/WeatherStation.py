# ตัวอย่างสถานีวัดอากาศโรงเรียน: อุณหภูมิ ความชื้น แสง และปริมาณน้ำฝน (WeatherStation)
# ต้นฉบับ C++: arduino_examples/16.Farm/WeatherStation/WeatherStation.ino  (เขียนเพิ่มในเวอร์ชัน 2.5 จากรูปสถานีวัดอากาศที่ครูส่งมา)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: อ่านค่า DHT22 และวัดปริมาณน้ำฝน และแสง LDR
# ขา: dht22.SIG=DHT_PIN, rain_gauge.SIG=RAIN_PIN, ldr.SIG=LIGHT_PIN
#
# ติดตั้ง: DHT22 อยู่ในโล่กันแดด (ชามพลาสติกขาวซ้อนกัน) สูงจากพื้นประมาณ 1.5 เมตร
#          เครื่องวัดน้ำฝนแบบถังกระดก ตั้งให้ได้ระดับน้ำ ห่างจากหลังคาและต้นไม้
#          LDR หันขึ้นฟ้า ไม่โดนเงาเสา
from machine import Pin, ADC, RTC
import dht
import time

DHT_PIN = 27
RAIN_PIN = 26
LIGHT_PIN = 34
MM_PER_TIP = 0.2             # ดูในคู่มือเครื่องวัดน้ำฝน (บางรุ่น 0.254)
RAINING_WINDOW_S = 600       # ถ้ามีการกระดกภายใน 10 นาทีที่ผ่านมา ถือว่าฝนกำลังตก


def make_adc(pin):
    if pin == "A0":
        return ADC(0)
    adc = ADC(Pin(pin))
    if hasattr(adc, "atten"):
        adc.atten(ADC.ATTN_11DB)
    return adc


sensor = dht.DHT22(Pin(DHT_PIN))
light_adc = make_adc(LIGHT_PIN)
rtc = RTC()
rain_pin = Pin(RAIN_PIN, Pin.IN, Pin.PULL_UP)
tips_today = 0
last_tip = None
today = rtc.datetime()[2]


def on_tip(p):
    """ถังกระดก 1 ครั้ง = ฝน MM_PER_TIP มม. (ไม่นับซ้ำภายใน 0.2 วินาที เพราะสวิตช์เด้ง)"""
    global tips_today, last_tip
    now = time.ticks_ms()
    if last_tip is None or time.ticks_diff(now, last_tip) > 200:
        tips_today += 1
        last_tip = now


rain_pin.irq(trigger=Pin.IRQ_FALLING, handler=on_tip)

while True:
    d = rtc.datetime()[2]
    if d != today:                        # ขึ้นวันใหม่: เริ่มนับฝนใหม่
        print("ฝนเมื่อวาน (มม.)", round(tips_today * MM_PER_TIP, 1))
        tips_today, today = 0, d
    raining = last_tip is not None and time.ticks_diff(time.ticks_ms(), last_tip) < RAINING_WINDOW_S * 1000
    try:
        sensor.measure()
        print("temp_c:", sensor.temperature())
        print("humidity:", sensor.humidity())
    except OSError:
        print("อ่าน DHT22 ไม่ได้")
    print("light:", light_adc.read_u16() * 100 // 65535)
    print("rain_mm:", round(tips_today * MM_PER_TIP, 1))
    print("raining:", 1 if raining else 0)
    time.sleep(5)

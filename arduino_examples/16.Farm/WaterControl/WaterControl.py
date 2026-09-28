# ตัวอย่างเกษตรอัจฉริยะ: ระบบควบคุมน้ำ ดินแห้ง + น้ำในถังพอ จึงรดน้ำ (WaterControl)
# ต้นฉบับ C++: arduino_examples/16.Farm/WaterControl/WaterControl.ino  (โครงงาน ทสรช.: ระบบควบคุมน้ำการเกษตรอัจฉริยะ ร.ร.โสตศึกษาจังหวัดเพชรบูรณ์)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: อ่านความชื้นในดิน และระยะทางด้วยอัลตราโซนิก ให้รีเลย์ทำงาน
# ขา: soil.SIG=SOIL_PIN, hc_sr04.TRIG=TRIG_PIN, hc_sr04.ECHO=ECHO_PIN, relay.SIG=PUMP_PIN
#
# ติดเซนเซอร์อัลตราโซนิกที่ฝาถังน้ำ หันลงหาผิวน้ำ
#
# สิ่งที่แก้จากต้นฉบับ
#   1) อัลตราโซนิกวัด "ระยะจากฝาถังถึงผิวน้ำ" ยิ่งน้ำน้อย ระยะยิ่งมาก ต้นฉบับใช้ waterLevel > 10 ว่าน้ำพอ
#      ซึ่งกลับกัน ตัวอย่างนี้คำนวณ ความลึกน้ำ = ความสูงถัง - ระยะที่วัดได้
#   2) ถ้าเสียงสะท้อนไม่กลับมา (ได้ค่า -1) ถือว่าไม่รู้ระดับน้ำ ไม่เปิดปั๊ม
#   3) ความชื้นดินแปลงเป็น % (ดินเปียก = ค่าสูง)
from machine import Pin, ADC, time_pulse_us
import time

SOIL_PIN = 34
TRIG_PIN = 4
ECHO_PIN = 27
PUMP_PIN = 18
TANK_HEIGHT_CM = 60          # ความสูงจากเซนเซอร์ถึงก้นถัง (วัดจริง)
MIN_WATER_CM = 10            # น้ำต่ำกว่านี้ห้ามเปิดปั๊ม (กันปั๊มไหม้)
DRY_PERCENT = 35
RELAY_ON, RELAY_OFF = 0, 1


def make_adc(pin):
    if pin == "A0":
        return ADC(0)
    adc = ADC(Pin(pin))
    if hasattr(adc, "atten"):
        adc.atten(ADC.ATTN_11DB)
    return adc


soil_adc = make_adc(SOIL_PIN)
trig = Pin(TRIG_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)
pump = Pin(PUMP_PIN, Pin.OUT, value=RELAY_OFF)


def distance_cm():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    t = time_pulse_us(echo, 1, 30000)          # รอเสียงสะท้อนไม่เกิน 30 มิลลิวินาที
    return -1 if t < 0 else t * 0.0343 / 2


while True:
    soil = 100 - soil_adc.read_u16() * 100 // 65535
    d = distance_cm()
    water_cm = TANK_HEIGHT_CM - d if d > 0 else -1
    enough_water = water_cm >= MIN_WATER_CM
    pump.value(RELAY_ON if (soil < DRY_PERCENT and enough_water) else RELAY_OFF)
    print("soil:", soil)
    print("water_cm:", round(water_cm, 1))
    if not enough_water:
        print("น้ำในถังน้อยหรือวัดไม่ได้ ไม่เปิดปั๊ม")
    time.sleep(2)

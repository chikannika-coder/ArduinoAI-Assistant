# ตัวอย่างต่อยอดหุ่นยนต์บีม: อ่านค่าเซนเซอร์ซ้าย/ขวา (BeamSensorRead)
# ต้นฉบับ C++: arduino_examples/15.Robot/BeamSensorRead/BeamSensorRead.ino  (เขียนเพิ่มในเวอร์ชัน 2.4)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: อ่านค่าเซนเซอร์หุ่นบีม
# ขา: beam_ir.SIG=LEFT_SENSOR
# ขาเพิ่ม: RIGHT_SENSOR=adc
#
# ใช้แผงเซนเซอร์อินฟราเรด 2 แผงที่บัดกรีไว้ตอนทำหุ่นยนต์บีม (ถอดถ่านออกก่อนต่อสาย)
#   สายเขียว (+)   -> ขา 3V3 ของบอร์ด  (ห้ามต่อถ่าน 4.5V แรงดันจะเกินขา ADC)
#   สายเหลือง (−)  -> GND ของบอร์ด
#   สายขาว (OUT)   -> ขา ADC (ภาพการต่อสายแสดงข้างซ้าย ข้างขวาต่อแบบเดียวกันที่ขา RIGHT_SENSOR)
#   ตัวต้านทานปรับค่าได้ 50k ต้องต่อระหว่างสายขาวกับ GND เหมือนในหุ่นบีม
#
# วิธีใช้: เปิดกราฟในแท็บ ③  วางเซนเซอร์บนพื้นขาว ดูค่า แล้ววางบนเส้นดำ ดูค่า
#          ค่ากึ่งกลางของสองค่านี้คือ THRESHOLD ที่จะใช้ในตัวอย่าง BeamLineFollower
from machine import Pin, ADC
import time

LEFT_SENSOR = 34             # สายขาวของเซนเซอร์ซ้าย
RIGHT_SENSOR = 35            # สายขาวของเซนเซอร์ขวา


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


left_adc = make_adc(LEFT_SENSOR)
right_adc = make_adc(RIGHT_SENSOR)

while True:
    left = analog_read(left_adc)     # พื้นขาว = ค่าสูง (แสงสะท้อนมาก), เส้นดำ = ค่าต่ำ
    right = analog_read(right_adc)
    print("left:", left)
    print("right:", right)
    time.sleep_ms(100)

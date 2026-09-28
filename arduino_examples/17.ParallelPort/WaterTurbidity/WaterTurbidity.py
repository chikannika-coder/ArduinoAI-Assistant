# จาก Turbo C พอร์ตขนาน สู่ MicroPython: น้ำใส / น้ำขุ่น (WaterTurbidity)
# ต้นฉบับ Turbo C: arduino_examples/17.ParallelPort/WaterTurbidity/WaterTurbidity.c  (โครงงาน Water-Fail ของครู)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: ถ้าน้ำขุ่นมากกว่า 40 ให้รีเลย์ทำงาน
# ขา: turbidity.SIG=TURBID_PIN, relay.SIG=PUMP_PIN
#
# ของเดิมอ่านขา S5 ของพอร์ตขนาน (บิต 32) ได้แค่ "ใส" หรือ "ขุ่น" แล้วเปิดขา D0 สั่งปั๊ม/วาล์ว
#   if ((inportb(0x379) & 32) == 32) WATER = 1;      ->   turbid = turbidity > TURBID_LEVEL
#   outport(0x378, 1)  /  outport(0x378, 0)          ->   pump.value(RELAY_ON / RELAY_OFF)
# บอร์ดสมัยใหม่มีขาแอนะล็อก (ADC) จึงอ่านความขุ่นเป็นตัวเลข 0-100 และตั้งเกณฑ์เองได้ ไม่ต้องปรับวงจรเปรียบเทียบ
from machine import Pin, ADC
import time

TURBID_PIN = 34
PUMP_PIN = 4
TURBID_LEVEL = 40            # ขุ่นเกินนี้เปิดปั๊มกรอง/ปล่อยน้ำ (ทดลองกับน้ำจริงแล้วปรับ)
RELAY_ON, RELAY_OFF = 0, 1


def make_adc(pin):
    if pin == "A0":
        return ADC(0)
    adc = ADC(Pin(pin))
    if hasattr(adc, "atten"):
        adc.atten(ADC.ATTN_11DB)
    return adc


sensor = make_adc(TURBID_PIN)
pump = Pin(PUMP_PIN, Pin.OUT, value=RELAY_OFF)

while True:
    turbidity = 100 - sensor.read_u16() * 100 // 65535   # แสงผ่านน้อย = ขุ่นมาก
    water = 1 if turbidity > TURBID_LEVEL else 0         # ตัวแปร WATER ของเดิม: 0 = น้ำใส, 1 = น้ำขุ่น
    pump.value(RELAY_ON if water else RELAY_OFF)
    print("turbidity:", turbidity)
    print("water:", water)
    time.sleep_ms(500)

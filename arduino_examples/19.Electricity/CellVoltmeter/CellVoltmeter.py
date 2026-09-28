# พื้นฐานไฟฟ้า: วัดไฟจากเซลล์ไฟฟ้าทำเอง (มะนาว / น้ำเกลือ) (CellVoltmeter)
# ต้นฉบับ C++: arduino_examples/19.Electricity/CellVoltmeter/CellVoltmeter.ino  (เขียนเพิ่มในเวอร์ชัน 2.7)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# ขาเพิ่ม: CELL_PIN=adc
#
# ทำเซลล์ไฟฟ้า: เสียบแผ่นสังกะสี (ตะปูชุบสังกะสี) กับแผ่นทองแดง (เหรียญ/ลวดทองแดง) ลงในมะนาวหรือน้ำเกลือ ห่างกันเล็กน้อย
# ต่อสาย: ทองแดง (ขั้วบวก) -> ขา CELL_PIN, สังกะสี (ขั้วลบ) -> GND
# ทดลอง: เปลี่ยนโลหะ เปลี่ยนน้ำ (น้ำเปล่า น้ำเกลือ น้ำส้มสายชู) ต่อ 2 เซลล์อนุกรม แล้วดูกราฟในแท็บ ③
# ⚠ วัดได้ไม่เกิน 3.3V ห้ามต่อถ่านหรือแหล่งไฟที่แรงกว่านี้เข้าขาบอร์ด ห้ามกินมะนาวที่ใช้ทดลองแล้ว
from machine import Pin, ADC
import time

CELL_PIN = 34
SAMPLES = 20                  # เฉลี่ยหลายครั้งให้ค่านิ่ง


def make_adc(pin):
    if pin == "A0":
        return ADC(0)
    adc = ADC(Pin(pin))
    if hasattr(adc, "atten"):
        adc.atten(ADC.ATTN_11DB)
    return adc


cell = make_adc(CELL_PIN)
while True:
    total = 0
    for _ in range(SAMPLES):
        total += cell.read_u16()
        time.sleep_ms(5)
    volts = total / SAMPLES * 3.3 / 65535
    print("volts:", round(volts, 3))
    time.sleep_ms(400)

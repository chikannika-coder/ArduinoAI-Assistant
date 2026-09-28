# พื้นฐานไฟฟ้า: วัดความต้านทานของไส้ดินสอและลวด (ResistanceMeter)
# ต้นฉบับ C++: arduino_examples/19.Electricity/ResistanceMeter/ResistanceMeter.ino  (เขียนเพิ่มในเวอร์ชัน 2.7)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# ขาเพิ่ม: SENSE_PIN=adc
#
# วงจรแบ่งแรงดัน: 3V3 -> สิ่งที่ต้องการวัด (Rx) -> ขา SENSE_PIN -> ตัวต้านทานรู้ค่า 10kΩ -> GND
# ทดลอง: ขีดเส้นดินสอ 2B / HB บนกระดาษ แตะปลายสายสองข้างของเส้น ลองเปลี่ยนความยาวเส้น
#         เส้นยาวขึ้น ความต้านทานมากขึ้น ไฟฟ้าผ่านยากขึ้น (หลอดไฟจะหรี่ลง = หลักการของตัวหรี่ไฟ)
from machine import Pin, ADC
import time

SENSE_PIN = 34
R_KNOWN = 10000               # โอห์ม ตัวต้านทานที่ต่อลง GND


def make_adc(pin):
    if pin == "A0":
        return ADC(0)
    adc = ADC(Pin(pin))
    if hasattr(adc, "atten"):
        adc.atten(ADC.ATTN_11DB)
    return adc


adc = make_adc(SENSE_PIN)
while True:
    raw = sum(adc.read_u16() for _ in range(10)) / 10
    if raw < 300:
        print("ไม่มีไฟผ่าน (วงจรขาด หรือเป็นฉนวน)")
        ohms = -1
    else:
        ohms = R_KNOWN * (65535 - raw) / raw        # จากสูตรแบ่งแรงดัน V = 3.3 * Rk / (Rx + Rk)
    print("ohms:", round(ohms))
    time.sleep_ms(300)

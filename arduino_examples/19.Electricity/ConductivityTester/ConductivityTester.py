# พื้นฐานไฟฟ้า: เครื่องทดสอบตัวนำ / ฉนวน (ConductivityTester)
# ต้นฉบับ C++: arduino_examples/19.Electricity/ConductivityTester/ConductivityTester.ino  (เขียนเพิ่มในเวอร์ชัน 2.7)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: ปรับไฟ LED ด้วย potentiometer
# ขา: potentiometer.SIG=PROBE_PIN, led.SIG=LED_PIN
#
# ของเดิมในห้องเรียน: ต่อถ่าน หลอดไฟ และช่องว่าง 2 ปลาย เอาวัสดุมาวางคร่อม หลอดติด = ตัวนำ
# แบบใช้บอร์ด: บอร์ดวัดได้ละเอียดกว่า บอกได้ว่า "นำได้ดี / นำได้บ้าง / ไม่นำ"
# ต่อสาย (ภาพการต่อสายใช้ตัวต้านทานปรับค่าแทนชั่วคราว ให้ต่อจริงตามนี้)
#   สายปลาย A  -> 3V3
#   สายปลาย B  -> ขา PROBE_PIN และต่อตัวต้านทาน 10kΩ จากขา PROBE_PIN ลง GND
#   เอาวัสดุ (ช้อน ยางลบ ไส้ดินสอ น้ำเกลือ ...) มาแตะปลาย A กับ B พร้อมกัน
# ⚠ ใช้ไฟจากบอร์ด (3.3V) เท่านั้น ห้ามทดลองกับไฟบ้านเด็ดขาด
from machine import Pin, ADC
import time

PROBE_PIN = 34
LED_PIN = 4


def make_adc(pin):
    if pin == "A0":
        return ADC(0)
    adc = ADC(Pin(pin))
    if hasattr(adc, "atten"):
        adc.atten(ADC.ATTN_11DB)
    return adc


probe = make_adc(PROBE_PIN)
led = Pin(LED_PIN, Pin.OUT)
last = ""
while True:
    conduct = probe.read_u16() * 100 // 65535      # 0 = ไม่มีไฟผ่าน, 100 = ไฟผ่านเต็มที่
    if conduct > 80:
        result = "ตัวนำที่ดี (โลหะ)"
    elif conduct > 10:
        result = "นำไฟฟ้าได้บ้าง (ไส้ดินสอ น้ำเกลือ ผิวหนัง)"
    else:
        result = "ฉนวน (ไฟฟ้าผ่านไม่ได้)"
    led.value(1 if conduct > 10 else 0)
    print("conduct:", conduct)
    if result != last:
        print(result)
        last = result
    time.sleep_ms(200)

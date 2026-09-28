# ตัวอย่างเกษตรอัจฉริยะ: บ่อกุ้งอัจฉริยะ (ShrimpPond)
# ต้นฉบับ C++: arduino_examples/16.Farm/ShrimpPond/ShrimpPond.ino  (โครงงาน ทสรช.: บ่อกุ้งอัจฉริยะ ร.ร.สมบูรณ์ศาสน์ จ.ยะลา)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: อ่านค่า DS18B20 และค่า pH ด้วย PH-4502C และค่า DO ให้รีเลย์ทำงาน
# ขา: ds18b20.SIG=TEMP_PIN, ph_sensor.SIG=PH_PIN, do_sensor.SIG=DO_PIN, relay.SIG=AERATOR_PIN
# ขาเพิ่ม: FEEDER_PIN=pwm
#
# สิ่งที่แก้จากต้นฉบับ
#   1) ต้นฉบับเทียบค่า DO เป็นโวลต์ (0-5) กับ 5 จึงเป็นจริงเกือบตลอด เครื่องตีน้ำเปิดทั้งวัน
#      ตัวอย่างนี้แปลงเป็น mg/L จากการปรับเทียบในอากาศ และคิดตามอุณหภูมิน้ำ
#   2) ต้นฉบับแสดง pH เป็นโวลต์ ตัวอย่างนี้แปลงเป็นค่า pH (ต้องปรับเทียบด้วยน้ำยา pH 7 และ pH 4)
#   3) หัววัด pH และ DO ให้แรงดันได้ถึง 5V ต้องต่อตัวแบ่งแรงดันก่อนเข้า ESP32/Pico
#   4) ต้นฉบับประกาศขาอัลตราโซนิกไว้แต่ไม่ได้ใช้ ตัวอย่างนี้ตัดออกเพื่อให้โค้ดสั้นลง
from machine import Pin, ADC, PWM
import onewire, ds18x20
import time

TEMP_PIN = 27
PH_PIN = 34
DO_PIN = 35
AERATOR_PIN = 4
FEEDER_PIN = 18
DIV = 2.0                     # ตัวแบ่งแรงดัน 10k+10k (บอร์ด 5V ไม่ต้องแบ่ง ใช้ 1.0)
PH_MID_V = 2.5                # แรงดันเมื่อจุ่มน้ำยา pH 7
PH_SLOPE = 0.18               # แรงดันเปลี่ยนต่อ 1 pH (หาจากน้ำยา pH 4)
DO_CAL_MV = 1600              # mV ของหัววัด DO ตอนปรับเทียบในอากาศ (ออกซิเจนอิ่มตัว)
DO_CAL_TEMP = 28              # อุณหภูมิตอนปรับเทียบ
DO_LOW, DO_OK = 4.0, 5.5      # mg/L: ต่ำกว่า 4 เปิดเครื่องตีน้ำ จนถึง 5.5 จึงปิด
FEED_EVERY_H = 6
RELAY_ON, RELAY_OFF = 0, 1


def make_adc(pin):
    if pin == "A0":
        return ADC(0)
    adc = ADC(Pin(pin))
    if hasattr(adc, "atten"):
        adc.atten(ADC.ATTN_11DB)
    return adc


def volts(adc):
    return adc.read_u16() * 3.3 / 65535 * DIV


def do_saturation(t):
    """ออกซิเจนละลายน้ำสูงสุด (mg/L) ที่อุณหภูมิ t องศา (น้ำจืด ความดันปกติ)"""
    return 14.652 - 0.41022 * t + 0.007991 * t * t - 0.000077774 * t * t * t


ds = ds18x20.DS18X20(onewire.OneWire(Pin(TEMP_PIN)))
roms = ds.scan()
ph_adc = make_adc(PH_PIN)
do_adc = make_adc(DO_PIN)
aerator = Pin(AERATOR_PIN, Pin.OUT, value=RELAY_OFF)
feeder = PWM(Pin(FEEDER_PIN), freq=50)
aerating = False
last_feed = time.ticks_ms()


def servo_angle(angle):
    feeder.duty_u16((500 + angle * 2000 // 180) * 65535 // 20000)


servo_angle(0)
while True:
    temp = 28.0
    if roms:
        ds.convert_temp()
        time.sleep_ms(750)
        temp = ds.read_temp(roms[0])
    ph = 7 + (PH_MID_V - volts(ph_adc)) / PH_SLOPE
    do_mv = volts(do_adc) * 1000                   # แรงดันจากหัววัด DO (mV)
    sat_mv = DO_CAL_MV + 35 * (temp - DO_CAL_TEMP)  # แรงดันตอนอิ่มตัว เปลี่ยนประมาณ 35 mV ต่อองศา
    do_mgl = do_mv * do_saturation(temp) / sat_mv
    aerating = do_mgl < DO_LOW or (aerating and do_mgl < DO_OK)
    aerator.value(RELAY_ON if aerating else RELAY_OFF)
    if time.ticks_diff(time.ticks_ms(), last_feed) >= FEED_EVERY_H * 3600 * 1000:
        last_feed = time.ticks_ms()
        servo_angle(90)
        time.sleep(5)
        servo_angle(0)
    print("temp_c:", round(temp, 1))
    print("ph:", round(ph, 2))
    print("do_mgl:", round(do_mgl, 2))
    time.sleep(2)

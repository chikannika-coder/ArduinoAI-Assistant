# ตัวอย่างเกษตรอัจฉริยะ: หุ่นไล่กาอัจฉริยะ (Scarecrow)
# ต้นฉบับ C++: arduino_examples/16.Farm/Scarecrow/Scarecrow.ino  (โครงงาน ทสรช.: หุ่นไล่กาอัจฉริยะเพื่อช่วยเกษตรกร ร.ร.ราชประชานุเคราะห์ 37)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: มีคนเคลื่อนไหว อ่านระยะทางอัลตราโซนิก ให้ buzzer และ LED และ servo ทำงาน
# ขา: pir.SIG=PIR_PIN, hc_sr04.TRIG=TRIG_PIN, hc_sr04.ECHO=ECHO_PIN, buzzer.SIG=BUZZER_PIN, led.SIG=LED_PIN, servo.SIG=SERVO_PIN
#
# สิ่งที่แก้จากต้นฉบับ
#   1) ต้นฉบับใช้ pulseIn ไม่กำหนดเวลารอ ถ้าไม่มีเสียงสะท้อนโปรแกรมจะค้าง 1 วินาที ตัวอย่างนี้รอไม่เกิน 30 มิลลิวินาที
#   2) เพิ่มการโบกแขนไปมา 3 ครั้ง และพักระหว่างรอบ (นกชินกับเสียงเดิม ๆ ถ้าดังตลอด)
from machine import Pin, PWM, time_pulse_us
import time

PIR_PIN = 27
TRIG_PIN = 4
ECHO_PIN = 26
BUZZER_PIN = 18
LED_PIN = 19
SERVO_PIN = 23
NEAR_CM = 50                 # สิ่งมีชีวิตเข้าใกล้กว่านี้จึงไล่
REST_S = 5                   # พักหลังไล่แต่ละครั้ง

pir = Pin(PIR_PIN, Pin.IN)
trig = Pin(TRIG_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)
buzzer = Pin(BUZZER_PIN, Pin.OUT)
led = Pin(LED_PIN, Pin.OUT)
servo = PWM(Pin(SERVO_PIN), freq=50)


def servo_angle(angle):
    servo.duty_u16((500 + angle * 2000 // 180) * 65535 // 20000)


def distance_cm():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    t = time_pulse_us(echo, 1, 30000)
    return -1 if t < 0 else t * 0.0343 / 2


def scare_away():
    buzzer.value(1)
    led.value(1)
    for _ in range(3):           # โบกแขนไปมา
        servo_angle(120)
        time.sleep_ms(300)
        servo_angle(30)
        time.sleep_ms(300)
    buzzer.value(0)
    led.value(0)
    servo_angle(0)


servo_angle(0)
while True:
    motion = pir.value()
    d = distance_cm() if motion else -1
    print("motion:", motion)
    print("distance_cm:", round(d, 1))
    if motion and 0 < d < NEAR_CM:
        scare_away()
        time.sleep(REST_S)
    time.sleep_ms(100)

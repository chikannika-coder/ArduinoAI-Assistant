# พื้นฐานไฟฟ้า: ส่งสัญญาณรหัสมอร์สด้วยไฟและเสียง (MorseCode)
# ต้นฉบับ C++: arduino_examples/19.Electricity/MorseCode/MorseCode.ino  (เขียนเพิ่มในเวอร์ชัน 2.7)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: ให้ LED และ buzzer ทำงาน
# ขา: led.SIG=LED_PIN, buzzer.SIG=BUZZER_PIN
#
# ของเดิม: ต่อถ่าน สวิตช์ และหลอดไฟ/ออด แล้วกดสวิตช์ส่งจุด (สั้น) ขีด (ยาว) ตามรหัสของ Samuel Morse
# แบบใช้บอร์ด: บอร์ดส่งข้อความให้เอง ไฟกะพริบและเสียงดังพร้อมกัน นักเรียนที่ไม่ได้ยินเสียงอ่านจากไฟได้
# ลองเปลี่ยน MESSAGE แล้วให้เพื่อนถอดรหัส
from machine import Pin
import time

LED_PIN = 4
BUZZER_PIN = 18
MESSAGE = "SOS"
UNIT_MS = 200                 # จุด = 1 หน่วย, ขีด = 3 หน่วย, เว้นระหว่างตัวอักษร = 3 หน่วย, ระหว่างคำ = 7 หน่วย

MORSE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.", "G": "--.", "H": "....", "I": "..",
    "J": ".---", "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
    "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--", "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-", "5": ".....", "6": "-....",
    "7": "--...", "8": "---..", "9": "----.",
}
led = Pin(LED_PIN, Pin.OUT)
buzzer = Pin(BUZZER_PIN, Pin.OUT)


def signal(units):
    led.value(1)
    buzzer.value(1)
    time.sleep_ms(units * UNIT_MS)
    led.value(0)
    buzzer.value(0)
    time.sleep_ms(UNIT_MS)            # เว้นระหว่างจุด/ขีดในตัวอักษรเดียวกัน


while True:
    for ch in MESSAGE.upper():
        if ch == " ":
            time.sleep_ms(4 * UNIT_MS)
            continue
        code = MORSE.get(ch, "")
        print(ch, code)
        for mark in code:
            signal(1 if mark == "." else 3)
        time.sleep_ms(2 * UNIT_MS)
    time.sleep(2)

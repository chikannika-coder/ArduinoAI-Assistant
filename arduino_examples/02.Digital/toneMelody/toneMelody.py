# ตัวอย่าง Arduino -> MicroPython: เล่นทำนองเพลง (toneMelody)
# ต้นฉบับ C++: arduino_examples/02.Digital/toneMelody/toneMelody.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: เล่นโน้ต passive buzzer
# ขา: buzzer_passive.SIG=BUZZER_PIN
from machine import Pin, PWM
import time

BUZZER_PIN = 18

# ความถี่ของโน้ต (Hz) จากไฟล์ pitches.h ของต้นฉบับ
NOTE = {"C4": 262, "G3": 196, "A3": 220, "B3": 247, "REST": 0}
melody = ["C4", "G3", "G3", "A3", "G3", "REST", "B3", "C4"]
durations = [4, 8, 8, 4, 4, 4, 4, 4]         # 4 = โน้ตตัวดำ, 8 = เขบ็ด 1 ชั้น

bz = PWM(Pin(BUZZER_PIN))
bz.duty_u16(0)


def tone(freq, ms):
    """= tone(pin, freq, duration)"""
    if freq > 0:
        bz.freq(freq)
        bz.duty_u16(32768)
    time.sleep_ms(ms)
    bz.duty_u16(0)                             # = noTone(pin)


for note, d in zip(melody, durations):
    length = 1000 // d
    tone(NOTE[note], length)
    time.sleep_ms(int(length * 0.30))          # เว้นช่องระหว่างโน้ต

bz.deinit()
print("done: 1")

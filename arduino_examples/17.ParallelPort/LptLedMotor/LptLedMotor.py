# จาก Turbo C พอร์ตขนาน สู่ MicroPython: เปิด LED / มอเตอร์ (LptLedMotor)
# ต้นฉบับ Turbo C: arduino_examples/17.ParallelPort/LptLedMotor/LptLedMotor.c  (testoutportLed.c / testoutportMotor.c ของครู)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: ให้ LED ติด และกดปุ่ม
# ขา: led.SIG=D0_PIN, button.SIG=STOP_BTN
#
# เทียบกับของเดิม
#   Turbo C                          MicroPython
#   outport(0x378, 1);               d0.value(1)       ขา D0 (ขา 2 ของพอร์ตขนาน) -> ขาบอร์ด D0_PIN
#   do { } while(!kbhit());          while stop.value() == 1:   รอจนกดปุ่มบนบอร์ด (แทนการกดแป้นพิมพ์)
#   outport(0x378, 0);               d0.value(0)
# ถ้าจะต่อมอเตอร์ ต้องผ่านทรานซิสเตอร์หรือรีเลย์เหมือนสมัยพอร์ตขนาน ห้ามต่อมอเตอร์เข้าขาบอร์ดตรง ๆ
from machine import Pin
import time

D0_PIN = 4
STOP_BTN = 27

d0 = Pin(D0_PIN, Pin.OUT)
stop = Pin(STOP_BTN, Pin.IN, Pin.PULL_UP)

d0.value(1)                 # LED ติด / มอเตอร์หมุน
print("กดปุ่มเพื่อหยุด")
while stop.value() == 1:    # ยังไม่กดปุ่ม (ปุ่มต่อลง GND กดแล้วได้ 0)
    time.sleep_ms(20)
d0.value(0)
print("หยุดแล้ว")

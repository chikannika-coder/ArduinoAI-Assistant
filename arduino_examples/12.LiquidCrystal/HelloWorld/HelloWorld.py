# ตัวอย่าง Arduino -> MicroPython: สวัสดีชาวโลกบนจอ (HelloWorld)
# ต้นฉบับ C++: arduino_examples/12.LiquidCrystal/HelloWorld/HelloWorld.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# แผนขา: แสดงบนจอ OLED
# ขา: oled.SDA=SDA_PIN, oled.SCL=SCL_PIN
# ต้นฉบับใช้จอ LCD 16x2 แบบต่อสาย 12 เส้น ตัวอย่างนี้ใช้จอ OLED แบบ I2C (4 เส้น) ที่มีในคลังความรู้
# ติดตั้งไลบรารีก่อน: กดปุ่ม "📦 ติดตั้งไลบรารี" (mpremote mip install ssd1306)
from machine import Pin, I2C
import ssd1306
import time

SDA_PIN = 21
SCL_PIN = 22

i2c = I2C(0, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)      # = lcd.begin(16, 2)

start = time.ticks_ms()
while True:
    seconds = time.ticks_diff(time.ticks_ms(), start) // 1000
    oled.fill(0)
    oled.text("hello, world!", 0, 0)          # = lcd.print("hello, world!")
    oled.text(str(seconds), 0, 16)            # = lcd.setCursor(0, 1); lcd.print(millis()/1000)
    oled.show()
    print("seconds:", seconds)
    time.sleep_ms(200)

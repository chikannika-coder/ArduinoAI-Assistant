# ตัวอย่าง Arduino -> MicroPython: เก็บค่าไว้แม้ปิดไฟ (eeprom_write)
# ต้นฉบับ C++: arduino_examples/14.EEPROM/eeprom_write/eeprom_write.ino  (Arduino IDE 1.6.0)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# MicroPython ไม่มี EEPROM แต่มีระบบไฟล์ในบอร์ด ใช้ไฟล์เก็บค่าที่ต้องจำไว้แม้ปิดไฟ
# ตัวอย่างนี้นับจำนวนครั้งที่เปิดบอร์ด (ถอดสาย USB แล้วเสียบใหม่ ค่าจะเพิ่มขึ้น)
# ถ้าต้องการให้ทำงานเองตอนเปิดบอร์ด ให้กดปุ่ม "⬆ อัปโหลดเป็น main.py"
import time

FILE = "boot_count.txt"

try:
    with open(FILE) as f:                  # = EEPROM.read(addr)
        count = int(f.read())
except (OSError, ValueError):              # ยังไม่เคยมีไฟล์
    count = 0

count += 1
with open(FILE, "w") as f:                 # = EEPROM.write(addr, value)
    f.write(str(count))

# ข้อควรระวัง: หน่วยความจำแฟลชเขียนซ้ำได้จำนวนจำกัด อย่าเขียนไฟล์ในลูปที่วนเร็ว ๆ
while True:
    print("boot_count:", count)
    time.sleep(2)

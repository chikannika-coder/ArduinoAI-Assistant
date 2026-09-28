# มือหุ่นยนต์ 5 นิ้ว รับคำสั่งผ่าน Wi-Fi (UDP) พร้อมระบบหยุดเมื่อสัญญาณหาย (RobotHandWiFi)
# ต้นฉบับ C++: arduino_examples/18.RobotHand/RobotHandWiFi/RobotHandWiFi.ino  (ESP32 + ESP32Servo)
# เลขขาด้านล่างโปรแกรมเลือกให้ตามบอร์ดที่เลือกตอนเปิดไฟล์
# ขาเพิ่ม: SERVO_PINS=pwm*5@servo:โป้ง|ชี้|กลาง|นาง|ก้อย
#
# หลักสูตรควบคุมแขนกลระยะไกล โมดูล 1 (ชั่วโมงที่ 3-6): ESP32 ต่อ Wi-Fi รับคำสั่งจากคอมพิวเตอร์/Raspberry Pi
# ใช้กับบอร์ดที่มี Wi-Fi (ESP32 ทุกรุ่น, Pico W)
#   1) ใส่ชื่อและรหัส Wi-Fi ด้านล่าง แล้วรัน ดู IP ของบอร์ดที่พิมพ์ออกมา
#   2) คอมพิวเตอร์ส่งข้อความ UDP ไปที่ IP นั้น พอร์ต 4210 เช่น ALL:T45,I30,M60,R20,P90 (ดู tools/hand_camera_udp.py)
#   3) ต้องส่งคำสั่งหรือ HB อย่างน้อยทุก 1 วินาที ถ้าหายไปนานกว่านั้น มือกางออกเอง (Fail-safe)
# คำสั่งเหมือนตัวอย่าง RobotHandSerial ทุกคำสั่ง และบอร์ดตอบกลับ OK / ERR ให้ผู้ส่งรู้ว่าได้รับแล้ว
#
# ⚠ อย่าเปิดพอร์ตนี้ออกอินเทอร์เน็ต (Port forwarding) ถ้าจะควบคุมจากคนละเครือข่าย ให้ผ่าน Raspberry Pi + Tailscale ตามหลักสูตร
from machine import Pin, PWM
import network
import socket
import time

SERVO_PINS = [4, 18, 19, 23, 25]   # [โป้ง, ชี้, กลาง, นาง, ก้อย]
WIFI_SSID = "ชื่อ Wi-Fi"
WIFI_PASSWORD = "รหัส Wi-Fi"
PORT = 4210
MIN_ANGLE, MAX_ANGLE = 0, 90
TIMEOUT_MS = 1000                  # ผ่านเครือข่ายให้สั้นกว่าแบบสาย USB
NAMES = "TIMRP"

servos = [PWM(Pin(p), freq=50) for p in SERVO_PINS]
angles = [0, 0, 0, 0, 0]
stopped = False


def write(i, angle):
    angle = max(MIN_ANGLE, min(MAX_ANGLE, int(angle)))
    servos[i].duty_u16((500 + angle * 2000 // 180) * 65535 // 20000)
    angles[i] = angle


def set_all(a):
    for i in range(5):
        write(i, a)


def handle(cmd):
    global stopped
    cmd = cmd.strip().upper()
    if cmd == "STOP":
        stopped = True
        set_all(MIN_ANGLE)
        return True
    if cmd == "RESUME":
        stopped = False
        return True
    if cmd in ("HB", ""):
        return True
    if stopped:
        return True
    try:
        if len(cmd) >= 3 and cmd[1] == ":" and cmd[0] in NAMES:
            write(NAMES.index(cmd[0]), int(cmd[2:]))
        elif cmd.startswith("ALL:"):
            for part in cmd[4:].split(","):
                part = part.strip()
                if len(part) >= 2 and part[0] in NAMES:
                    write(NAMES.index(part[0]), int(part[1:]))
        elif cmd.startswith("A:"):
            for i, v in enumerate(cmd[2:].split(",")[:5]):
                write(i, MAX_ANGLE - max(0, min(180, int(v))) * (MAX_ANGLE - MIN_ANGLE) // 180)
        elif cmd == "OPEN":
            set_all(MIN_ANGLE)
        elif cmd == "CLOSE":
            set_all(MAX_ANGLE)
        else:
            return False
    except ValueError:
        return False
    return True


set_all(MIN_ANGLE)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)
for _ in range(100):                          # รอเชื่อมต่อไม่เกิน 10 วินาที
    if wlan.isconnected():
        break
    time.sleep_ms(100)
if wlan.isconnected():
    print("ต่อ Wi-Fi แล้ว IP ของบอร์ด:", wlan.ifconfig()[0], "พอร์ต", PORT)
else:
    print("ต่อ Wi-Fi ไม่ได้ ตรวจชื่อและรหัส (ESP32 ใช้ได้เฉพาะ Wi-Fi 2.4 GHz)")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", PORT))
sock.settimeout(0.05)                          # รอข้อมูลสั้น ๆ แล้ววนไปตรวจ fail-safe
last_cmd = time.ticks_ms()
safe = True
n = 0
while True:
    try:
        data, addr = sock.recvfrom(256)
    except OSError:                            # หมดเวลารอ: ยังไม่มีข้อมูลใหม่
        data = None
    if data:
        ok = True
        for line in data.decode().splitlines():
            ok = handle(line) and ok
        last_cmd, safe = time.ticks_ms(), False
        sock.sendto(b"OK" if ok else b"ERR", addr)
    if not safe and time.ticks_diff(time.ticks_ms(), last_cmd) > TIMEOUT_MS:
        set_all(MIN_ANGLE)
        safe = True
        print("สัญญาณหาย กางมือแล้ว (Fail-safe)")
    n += 1
    if n % 20 == 0:
        for name, a in zip(("thumb", "index", "middle", "ring", "pinky"), angles):
            print("%s:" % name, a)
    time.sleep_ms(5)

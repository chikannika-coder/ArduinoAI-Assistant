# -*- coding: utf-8 -*-
"""กล้องคอมพิวเตอร์อ่านมือ -> ส่งมุมนิ้วไปมือหุ่นยนต์ (ArduinoAI 2.7, หลักสูตรควบคุมแขนกล ชั่วโมงที่ 7-10)

รันบนคอมพิวเตอร์ (Windows / Raspberry Pi) ไม่ใช่บนบอร์ด
  ติดตั้งครั้งเดียว:  py -3 -m pip install opencv-python mediapipe pyserial
  ส่งผ่าน Wi-Fi:      py -3 tools/hand_camera_udp.py --udp 192.168.1.50      (IP ที่ ESP32 พิมพ์ออกมา)
  ส่งผ่านสาย USB:     py -3 tools/hand_camera_udp.py --serial COM5
คีย์: q = ออก (ส่ง OPEN ก่อนออก), s = หยุดฉุกเฉิน (STOP), r = ทำงานต่อ (RESUME)

แนวคิดที่ใช้ (ตามหลักสูตร): วัดการงอนิ้วเป็นมุมต่อเนื่อง, dead zone ไม่ส่งถ้าเปลี่ยนน้อย, smoothing,
จำกัดอัตราส่ง 20 ครั้ง/วินาที, heartbeat HB ทุก 0.3 วินาที, ไม่เห็นมือ -> ไม่ส่งมุม (บอร์ดจะกางมือเองเมื่อหมดเวลา)
"""
import argparse
import math
import socket
import time

MIN_ANGLE, MAX_ANGLE = 0, 90
TIPS = [4, 8, 12, 16, 20]
PIPS = [3, 6, 10, 14, 18]
MCPS = [2, 5, 9, 13, 17]


def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def bend_ratio(lm, i):
    """0 = นิ้วเหยียด, 1 = งอสุด (เทียบระยะปลายนิ้วถึงข้อมือกับความยาวโคนนิ้ว ใช้ได้ทั้งมือซ้ายและขวา)"""
    wrist = lm[0]
    if i == 0:                      # นิ้วโป้ง: ปลายนิ้วเข้าใกล้โคนนิ้วก้อยเมื่องอ
        ref = dist(lm[5], lm[17]) or 1e-6
        r = dist(lm[4], lm[17]) / ref
        return max(0.0, min(1.0, (1.6 - r) / 0.9))
    ref = dist(wrist, lm[MCPS[i]]) or 1e-6
    r = dist(wrist, lm[TIPS[i]]) / ref
    return max(0.0, min(1.0, (1.9 - r) / 1.0))


class Sender:
    def __init__(self, udp=None, port=4210, serial_port=None):
        self.udp, self.port, self.ser = udp, port, None
        if udp:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if serial_port:
            import serial
            self.ser = serial.Serial(serial_port, 9600, timeout=0)
            time.sleep(2)            # Arduino รีเซ็ตตอนเปิดพอร์ต

    def send(self, line):
        data = (line + "\n").encode()
        if self.udp:
            self.sock.sendto(data, (self.udp, self.port))
        if self.ser:
            self.ser.write(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--udp", help="IP ของ ESP32")
    ap.add_argument("--port", type=int, default=4210)
    ap.add_argument("--serial", help="พอร์ต เช่น COM5 หรือ /dev/ttyUSB0")
    ap.add_argument("--camera", type=int, default=0)
    args = ap.parse_args()
    if not args.udp and not args.serial:
        ap.error("ต้องใส่ --udp <IP> หรือ --serial <พอร์ต>")

    import cv2
    import mediapipe as mp
    tx = Sender(args.udp, args.port, args.serial)
    hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.65, min_tracking_confidence=0.65)
    draw = mp.solutions.drawing_utils
    cap = cv2.VideoCapture(args.camera)
    smooth = [0.0] * 5
    sent = [None] * 5
    last_send = last_hb = 0.0
    stopped = False
    while True:
        ok, frame = cap.read()
        if not ok:
            print("อ่านกล้องไม่ได้")
            break
        frame = cv2.flip(frame, 1)
        res = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        now = time.time()
        if res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0].landmark
            draw.draw_landmarks(frame, res.multi_hand_landmarks[0], mp.solutions.hands.HAND_CONNECTIONS)
            for i in range(5):
                target = MIN_ANGLE + bend_ratio(lm, i) * (MAX_ANGLE - MIN_ANGLE)
                smooth[i] += (target - smooth[i]) * 0.4                     # smoothing
            angles = [int(round(a)) for a in smooth]
            changed = any(s is None or abs(a - s) >= 3 for a, s in zip(angles, sent))   # dead zone 3 องศา
            if changed and now - last_send >= 0.05 and not stopped:        # ไม่เกิน 20 ครั้ง/วินาที
                tx.send("ALL:" + ",".join("%s%d" % (n, a) for n, a in zip("TIMRP", angles)))
                sent, last_send = angles, now
            label = " ".join("%s%d" % (n, a) for n, a in zip("TIMRP", angles))
        else:
            label = "ไม่เห็นมือ"
        if now - last_hb >= 0.3 and res.multi_hand_landmarks and not stopped:
            tx.send("HB")                                                   # heartbeat
            last_hb = now
        cv2.putText(frame, ("STOP " if stopped else "") + label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow("Hand -> Robot (q=quit, s=STOP, r=RESUME)", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("s"):
            tx.send("STOP")
            stopped = True
        if key == ord("r"):
            tx.send("RESUME")
            stopped = False
    tx.send("OPEN")
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

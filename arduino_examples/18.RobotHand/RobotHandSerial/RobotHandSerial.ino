/*
  RobotHandSerial  (ArduinoAI 2.7 หมวด 18 มือหุ่นยนต์)
  แก้จาก pan_robot_hand2.ino ของครู (ไฟล์เดิมอยู่ในโฟลเดอร์เดียวกัน: pan_robot_hand2_original.ino)

  สิ่งที่แก้/เพิ่ม
   1) รับรูปแบบ "A:180,0,180,0,0" ที่หน้าเว็บกล้อง (hand_camera_servo_realtime_mediapipe.html) ส่งมาด้วย
      ของเดิมรับแค่ "T:45" และ "ALL:T45,..." มือจึงไม่ขยับเมื่อใช้กับหน้าเว็บ
      (180 = นิ้วเหยียด -> MIN_ANGLE, 0 = นิ้วงอ -> MAX_ANGLE)
   2) Fail-safe: ไม่มีคำสั่งเกิน 3 วินาที มือกางออกเอง
   3) E-Stop: "STOP" กางมือและไม่รับคำสั่งขยับจนกว่าจะส่ง "RESUME", "HB" = heartbeat
   4) ALL: ตัดคำสั่งด้วย indexOf แบบเดิมจะอ่านผิดถ้าส่งมาไม่ครบ 5 นิ้ว ตอนนี้อ่านได้ทุกจำนวน

  ขาเซอร์โว (Arduino Uno): โป้ง D10, ชี้ D9, กลาง D6, นาง D5, ก้อย D3 (เหมือนเดิม)
  ⚠ เซอร์โว 5 ตัวต้องใช้ไฟ 5V แยก (2-3A) และต่อ GND ร่วมกับ Arduino
*/
#include <Servo.h>

Servo fingers[5];
const int PINS[5] = {10, 9, 6, 5, 3};          // Thumb, Index, Middle, Ring, Pinky
const char NAMES[5] = {'T', 'I', 'M', 'R', 'P'};
const int MIN_ANGLE = 0;                        // Fully open
const int MAX_ANGLE = 90;                       // Fully closed
const unsigned long TIMEOUT_MS = 3000;          // 0 = ปิด fail-safe

int currentAngles[5] = {0, 0, 0, 0, 0};
bool stopped = false;
bool safeState = true;
unsigned long lastCmd = 0;

void writeFinger(int i, int angle) {
  angle = constrain(angle, MIN_ANGLE, MAX_ANGLE);
  fingers[i].write(angle);
  currentAngles[i] = angle;
}

void setAll(int angle) {
  for (int i = 0; i < 5; i++) writeFinger(i, angle);
}

int fingerIndex(char c) {
  for (int i = 0; i < 5; i++) if (NAMES[i] == c) return i;
  return -1;
}

void waveSequence() {
  for (int i = 4; i >= 0; i--) {
    writeFinger(i, MAX_ANGLE); delay(200);
    writeFinger(i, MIN_ANGLE); delay(200);
  }
}

void testSequence() {
  Serial.println("=== TESTING ALL FINGERS ===");
  for (int i = 0; i < 5; i++) {
    writeFinger(i, MAX_ANGLE); delay(500);
    writeFinger(i, MIN_ANGLE); delay(500);
  }
  Serial.println("=== TEST COMPLETE ===");
}

bool processCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();
  if (cmd.length() == 0) return false;
  if (cmd == "STOP") { stopped = true; setAll(MIN_ANGLE); Serial.println("E-STOP"); return true; }
  if (cmd == "RESUME") { stopped = false; Serial.println("RESUMED"); return true; }
  if (cmd == "HB") return true;
  if (stopped) return true;

  if (cmd.length() >= 3 && cmd.charAt(1) == ':' && fingerIndex(cmd.charAt(0)) >= 0) {   // T:45
    writeFinger(fingerIndex(cmd.charAt(0)), cmd.substring(2).toInt());
  } else if (cmd.startsWith("ALL:")) {                                                    // ALL:T45,I30,...
    String rest = cmd.substring(4) + ",";
    int start = 0, comma;
    while ((comma = rest.indexOf(',', start)) >= 0) {
      String part = rest.substring(start, comma);
      part.trim();
      if (part.length() >= 2 && fingerIndex(part.charAt(0)) >= 0)
        writeFinger(fingerIndex(part.charAt(0)), part.substring(1).toInt());
      start = comma + 1;
    }
  } else if (cmd.startsWith("A:")) {                                                      // A:180,0,... (หน้าเว็บ)
    String rest = cmd.substring(2) + ",";
    int start = 0, comma, i = 0;
    while ((comma = rest.indexOf(',', start)) >= 0 && i < 5) {
      int v = constrain(rest.substring(start, comma).toInt(), 0, 180);
      writeFinger(i++, MAX_ANGLE - (long)v * (MAX_ANGLE - MIN_ANGLE) / 180);
      start = comma + 1;
    }
  } else if (cmd == "OPEN" || cmd == "SEQ:OPEN") {
    setAll(MIN_ANGLE);
  } else if (cmd == "CLOSE") {
    setAll(MAX_ANGLE);
  } else if (cmd == "SEQ:WAVE") {
    waveSequence();
  } else if (cmd == "SEQ:FIST") {
    setAll(MAX_ANGLE); delay(1000); setAll(MIN_ANGLE); delay(1000);
  } else if (cmd == "TEST" || cmd == "SEQ:TEST") {
    testSequence();
  } else {
    Serial.print("ERR ");
    Serial.println(cmd);
    return false;
  }
  return true;
}

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < 5; i++) fingers[i].attach(PINS[i]);
  setAll(MIN_ANGLE);
  Serial.println("AI HAND CONTROLLER - READY");
  lastCmd = millis();
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    if (processCommand(command)) {
      lastCmd = millis();
      safeState = false;
    }
  }
  if (TIMEOUT_MS && !safeState && millis() - lastCmd > TIMEOUT_MS) {
    setAll(MIN_ANGLE);                         // ผู้ควบคุมหายไป: กางมือไว้ก่อน
    safeState = true;
    Serial.println("TIMEOUT");
  }
}

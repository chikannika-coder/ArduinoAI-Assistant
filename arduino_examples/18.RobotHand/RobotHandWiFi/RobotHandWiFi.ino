/*
  RobotHandWiFi  (ArduinoAI 2.7 หมวด 18 มือหุ่นยนต์) สำหรับบอร์ด ESP32 / ESP32-S2 / ESP32-S3
  รับคำสั่งผ่าน Wi-Fi แบบ UDP พอร์ต 4210 คำสั่งเหมือน RobotHandSerial และมี fail-safe 1 วินาที
  ติดตั้งไลบรารี "ESP32Servo" ใน Arduino IDE ก่อน (Servo.h ธรรมดาใช้กับ ESP32 ไม่ได้)
  ⚠ เซอร์โวใช้ไฟ 5V แยก ต่อ GND ร่วม ห้ามเลี้ยงจากขา 3V3 ของ ESP32
*/
#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>

const char* WIFI_SSID = "ชื่อ Wi-Fi";
const char* WIFI_PASSWORD = "รหัส Wi-Fi";
const int PORT = 4210;
const int PINS[5] = {4, 18, 19, 23, 25};       // Thumb, Index, Middle, Ring, Pinky
const char NAMES[5] = {'T', 'I', 'M', 'R', 'P'};
const int MIN_ANGLE = 0, MAX_ANGLE = 90;
const unsigned long TIMEOUT_MS = 1000;

Servo fingers[5];
WiFiUDP udp;
char packet[256];
bool stopped = false, safeState = true;
unsigned long lastCmd = 0;

void writeFinger(int i, int a) { fingers[i].write(constrain(a, MIN_ANGLE, MAX_ANGLE)); }
void setAll(int a) { for (int i = 0; i < 5; i++) writeFinger(i, a); }
int fingerIndex(char c) { for (int i = 0; i < 5; i++) if (NAMES[i] == c) return i; return -1; }

bool handle(String cmd) {
  cmd.trim(); cmd.toUpperCase();
  if (cmd == "STOP") { stopped = true; setAll(MIN_ANGLE); return true; }
  if (cmd == "RESUME") { stopped = false; return true; }
  if (cmd == "HB" || cmd.length() == 0) return true;
  if (stopped) return true;
  if (cmd.length() >= 3 && cmd.charAt(1) == ':' && fingerIndex(cmd.charAt(0)) >= 0) {
    writeFinger(fingerIndex(cmd.charAt(0)), cmd.substring(2).toInt());
  } else if (cmd.startsWith("ALL:")) {
    String rest = cmd.substring(4) + ",";
    int start = 0, comma;
    while ((comma = rest.indexOf(',', start)) >= 0) {
      String p = rest.substring(start, comma); p.trim();
      if (p.length() >= 2 && fingerIndex(p.charAt(0)) >= 0) writeFinger(fingerIndex(p.charAt(0)), p.substring(1).toInt());
      start = comma + 1;
    }
  } else if (cmd == "OPEN") { setAll(MIN_ANGLE);
  } else if (cmd == "CLOSE") { setAll(MAX_ANGLE);
  } else return false;
  return true;
}

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 5; i++) { fingers[i].setPeriodHertz(50); fingers[i].attach(PINS[i], 500, 2500); }
  setAll(MIN_ANGLE);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) { delay(200); Serial.print("."); }
  Serial.print("\nIP ของบอร์ด: "); Serial.println(WiFi.localIP());
  udp.begin(PORT);
}

void loop() {
  int size = udp.parsePacket();
  if (size > 0) {
    int n = udp.read(packet, sizeof(packet) - 1);
    packet[n] = 0;
    bool ok = handle(String(packet));
    lastCmd = millis(); safeState = false;
    udp.beginPacket(udp.remoteIP(), udp.remotePort());
    udp.print(ok ? "OK" : "ERR");
    udp.endPacket();
  }
  if (!safeState && millis() - lastCmd > TIMEOUT_MS) {
    setAll(MIN_ANGLE);
    safeState = true;
    Serial.println("Fail-safe: สัญญาณหาย กางมือแล้ว");
  }
}

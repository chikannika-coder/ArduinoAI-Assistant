// ฝึกหาจุดผิด (ArduinoAI 2.7.1): โค้ดรดน้ำต้นไม้นี้มีจุดผิดที่นักเรียนพบบ่อย 4 จุด
// เปิดไฟล์นี้ในแท็บ ① สร้างโค้ด → 📂 เปิดไฟล์ แล้วดูข้อความ 🩺 ด้านขวา
// เฉลยอยู่ท้ายไฟล์ (ลองหาเองก่อน)
#include <DHT.h>

#define DHTPIN 4
#define RELAY_PIN 4          // จุดผิด?
#define LED_PIN 13
#define BUZZER_PIN 8

DHT dht(DHTPIN, DHT11);

void setup() {
  Serial.begin(9600);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  dht.begin();
}

void loop() {
  float t = dht.readTemperature();
  int soil = analogRead(A0);
  Serial.println(t);
  if (soil > 700) {                  // ดินแห้ง
    digitalWrite(RELAY_PIN, HIGH);   // เปิดปั๊ม
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(RELAY_PIN, LOW);
    digitalWrite(LED_PIN, LOW);
  }
  delay(60000);
}

/* เฉลย
 1. DHTPIN กับ RELAY_PIN ใช้ขา 4 ซ้ำกัน  -> ย้ายรีเลย์ไปขาอื่น เช่น 7
 2. อ่าน DHT แล้วไม่ตรวจ isnan(t)          -> if (isnan(t)) { return; }
 3. รีเลย์ส่วนใหญ่ทำงานเมื่อสั่ง LOW       -> ลองสลับ HIGH / LOW
 4. delay(60000) บอร์ดหยุดรอ 1 นาที       -> ใช้ millis() หรือลดเวลารอ
 (BUZZER_PIN ประกาศไว้แต่ไม่ได้ใช้ ลบทิ้งได้)
*/

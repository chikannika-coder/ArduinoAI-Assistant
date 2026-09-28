/*
  CricketHouse  (ArduinoAI 2.5 หมวด 16 เกษตรอัจฉริยะ)
  โค้ดต้นฉบับจากโครงงานตู้เลี้ยงจิ้งหรีดอัตโนมัติ (ร.ร.ราชประชานุเคราะห์ 24 จ.พะเยา)
  งานอบรม ทสรช. 25-27 ก.ย. ที่ครูส่งมา (ไม่ได้แก้โค้ดด้านล่าง เก็บไว้เทียบ)

  จุดที่ควรแก้ (แก้แล้วในไฟล์ CricketHouse.py):
   - เปิดพัดลมเมื่อความชื้นต่ำ แต่พัดลมทำให้ความชื้นลดลงอีก
   - เช็ก minute() == 0 แต่ loop รอ 1 นาที บางวันจะข้ามนาทีนั้นไป
*/

#include <DHT.h>
#include <Wire.h>
#include <RTClib.h>

#define DHTPIN 2
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);
RTC_DS3231 rtc;

#define RELAY_HEAT 3
#define RELAY_FAN 4
#define RELAY_LIGHT 5
#define RELAY_FEED 6
#define RELAY_WATER 7

const float TEMP_SETPOINT = 28.0; // Desired temperature for crickets
const float HUMID_SETPOINT = 60.0; // Desired humidity

void setup() {
  pinMode(RELAY_HEAT, OUTPUT);
  pinMode(RELAY_FAN, OUTPUT);
  pinMode(RELAY_LIGHT, OUTPUT);
  pinMode(RELAY_FEED, OUTPUT);
  pinMode(RELAY_WATER, OUTPUT);
  
  dht.begin();
  rtc.begin();
}

void loop() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  // Temperature control
  if (temperature < TEMP_SETPOINT) {
    digitalWrite(RELAY_HEAT, HIGH);
  } else {
    digitalWrite(RELAY_HEAT, LOW);
  }

  // Humidity control
  if (humidity < HUMID_SETPOINT) {
    digitalWrite(RELAY_FAN, HIGH);
  } else {
    digitalWrite(RELAY_FAN, LOW);
  }

  // Simulate day/night using RTC
  DateTime now = rtc.now();
  if (now.hour() >= 6 && now.hour() <= 18) {
    digitalWrite(RELAY_LIGHT, HIGH);
  } else {
    digitalWrite(RELAY_LIGHT, LOW);
  }

  // Feed and water at specific times
  if (now.hour() == 8 && now.minute() == 0) {
    digitalWrite(RELAY_FEED, HIGH);
    delay(5000);
    digitalWrite(RELAY_FEED, LOW);
  }
  if (now.hour() == 10 && now.minute() == 0) {
    digitalWrite(RELAY_WATER, HIGH);
    delay(5000);
    digitalWrite(RELAY_WATER, LOW);
  }

  delay(60000); // Delay for 1 minute
}

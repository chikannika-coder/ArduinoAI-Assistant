/*
  CowFarm  (ArduinoAI 2.5 หมวด 16 เกษตรอัจฉริยะ)
  โค้ดต้นฉบับจากโครงงานฟาร์มวัวอัจฉริยะ (ร.ร.พระปริยัติธรรมวัดภูเก็ต จ.น่าน)
  งานอบรม ทสรช. 25-27 ก.ย. ที่ครูส่งมา (ไม่ได้แก้โค้ดด้านล่าง เก็บไว้เทียบ)

  จุดที่ควรแก้ (แก้แล้วในไฟล์ CowFarm.py):
   - ปั๊มเปิด/ปิดที่ค่าเดียวกัน น้ำกระเพื่อมทำให้ปั๊มติด-ดับถี่
   - ไม่มีการกันปั๊มเดินตัวเปล่าเมื่อน้ำไม่ไหล
*/

#include <DHT.h>
#define DHTPIN 2
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);
#define RELAY_PUMP 3
#define RELAY_FAN 4
#define WATER_SENSOR A0

const float TEMP_THRESHOLD = 28.0; // Example threshold in Celsius
const int WATER_LOW_THRESHOLD = 300; // Example threshold

void setup() {
  pinMode(RELAY_PUMP, OUTPUT);
  pinMode(RELAY_FAN, OUTPUT);
  dht.begin();
}

void loop() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  int waterLevel = analogRead(WATER_SENSOR);

  if (temperature > TEMP_THRESHOLD) {
    digitalWrite(RELAY_FAN, HIGH);
  } else {
    digitalWrite(RELAY_FAN, LOW);
  }

  if (waterLevel < WATER_LOW_THRESHOLD) {
    digitalWrite(RELAY_PUMP, HIGH); 
  } else {
    digitalWrite(RELAY_PUMP, LOW);
  }

  // Add logic for RFID reading, GPS tracking, accelerometer monitoring, and other functionalities.

  delay(10000); // Delay for 10 seconds
}

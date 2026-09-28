/*
  MushroomHouse  (ArduinoAI 2.5 หมวด 16 เกษตรอัจฉริยะ)
  โค้ดต้นฉบับจากโครงงานโรงเรือนเพาะเห็ดอัจฉริยะ (ร.ร.นันทบุรีวิทยา จ.น่าน)
  งานอบรม ทสรช. 25-27 ก.ย. ที่ครูส่งมา (ไม่ได้แก้โค้ดด้านล่าง เก็บไว้เทียบ)

  จุดที่ควรแก้ (แก้แล้วในไฟล์ MushroomHouse.py):
   - เปิด/ปิดที่ค่าเดียวกันพอดี (ไม่มีช่วงกันสั่น) รีเลย์จะติด-ดับถี่
   - ประกาศรีเลย์พัดลมไว้แต่ยังไม่ได้ใช้
   - ไม่ได้ตรวจว่าอ่าน DHT ได้หรือไม่ (isnan)
*/

#include <DHT.h>
#define DHTPIN 2
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);
#define RELAY_HEAT 3
#define RELAY_HUMID 4
#define RELAY_PUMP 5
#define RELAY_FAN 6
#define SOIL_SENSOR A0

const float TEMP_SETPOINT = 25.0;
const float HUMID_SETPOINT = 70.0;
const int SOIL_DRY_THRESHOLD = 300; // This might need calibration

void setup() {
  pinMode(RELAY_HEAT, OUTPUT);
  pinMode(RELAY_HUMID, OUTPUT);
  pinMode(RELAY_PUMP, OUTPUT);
  pinMode(RELAY_FAN, OUTPUT);
  dht.begin();
}

void loop() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  int soilMoisture = analogRead(SOIL_SENSOR);

  if (temperature < TEMP_SETPOINT) {
    digitalWrite(RELAY_HEAT, HIGH);
  } else {
    digitalWrite(RELAY_HEAT, LOW);
  }

  if (humidity < HUMID_SETPOINT) {
    digitalWrite(RELAY_HUMID, HIGH);
  } else {
    digitalWrite(RELAY_HUMID, LOW);
  }

  if (soilMoisture < SOIL_DRY_THRESHOLD) {
    digitalWrite(RELAY_PUMP, HIGH); // Water the plants
  } else {
    digitalWrite(RELAY_PUMP, LOW);
  }

  // Add logic for fan and lights as per requirements

  delay(10000); // Delay for 10 seconds
}

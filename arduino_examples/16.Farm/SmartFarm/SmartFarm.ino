/*
  SmartFarm  (ArduinoAI 2.5 หมวด 16 เกษตรอัจฉริยะ)
  โค้ดต้นฉบับจากโครงงานสมาร์ทฟาร์มโรงเรือนอัจฉริยะ (ร.ร.ราชประชานุเคราะห์ 66 จ.นราธิวาส)
  งานอบรม ทสรช. 25-27 ก.ย. ที่ครูส่งมา (ไม่ได้แก้โค้ดด้านล่าง เก็บไว้เทียบ)

  จุดที่ควรแก้ (แก้แล้วในไฟล์ SmartFarm.py):
   - analogRead < 300 ถือว่าดินแห้ง แต่เซนเซอร์ส่วนใหญ่ค่าสูงเมื่อแห้ง ทดสอบกับดินจริงก่อน
   - delay(60000) ทำให้บอร์ดไม่ตอบสนอง 1 นาที
   - ไม่ได้ตรวจว่าอ่าน DHT ได้หรือไม่ (isnan)
*/

#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT22
#define SOIL_MOISTURE_PIN A0
#define PUMP_PIN 3

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  pinMode(PUMP_PIN, OUTPUT);
  digitalWrite(PUMP_PIN, LOW); // Pump OFF
  
  dht.begin();
  Serial.begin(9600);
}

void loop() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  int soilMoisture = analogRead(SOIL_MOISTURE_PIN);

  if (soilMoisture < 300) {
    digitalWrite(PUMP_PIN, HIGH); // Pump ON
    delay(5000); 
    digitalWrite(PUMP_PIN, LOW); // Pump OFF
  }
  
  // Send data for monitoring or further processing
  Serial.print("Temperature: "); Serial.print(temperature);
  Serial.print(" Humidity: "); Serial.println(humidity);
  
  delay(60000); // Delay for 1 minute
}

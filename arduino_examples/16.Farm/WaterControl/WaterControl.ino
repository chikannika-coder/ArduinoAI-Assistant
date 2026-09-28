/*
  WaterControl  (ArduinoAI 2.5 หมวด 16 เกษตรอัจฉริยะ)
  โค้ดต้นฉบับจากโครงงานระบบควบคุมน้ำการเกษตรอัจฉริยะ (ร.ร.โสตศึกษาจังหวัดเพชรบูรณ์)
  งานอบรม ทสรช. 25-27 ก.ย. ที่ครูส่งมา (ไม่ได้แก้โค้ดด้านล่าง เก็บไว้เทียบ)

  จุดที่ควรแก้ (แก้แล้วในไฟล์ WaterControl.py):
   - อัลตราโซนิกวัดระยะถึงผิวน้ำ ยิ่งน้ำน้อยระยะยิ่งมาก waterLevel > 10 จึงแปลว่าน้ำ "น้อย" ไม่ใช่ "พอ"
   - pulseIn ไม่กำหนดเวลารอ ถ้าไม่มีเสียงสะท้อนจะค้าง 1 วินาทีและได้ระยะ 0
*/

#define SOIL_SENSOR_PIN A0
#define RELAY_PIN 3
#define TRIG_PIN 4
#define ECHO_PIN 5

void setup() {
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  Serial.begin(9600);
}

void loop() {
  int soilMoisture = analogRead(SOIL_SENSOR_PIN);
  float waterLevel = getWaterLevel();

  // If soil is dry and there's sufficient water in the reservoir, start irrigation
  if (soilMoisture < 500 && waterLevel > 10) {  // 500 and 10 are example thresholds; adjust as needed
    digitalWrite(RELAY_PIN, HIGH);  // Start the pump
  } else {
    digitalWrite(RELAY_PIN, LOW);   // Stop the pump
  }
  
  delay(5000);
}

float getWaterLevel() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  long duration = pulseIn(ECHO_PIN, HIGH);
  float distance = duration * 0.0344 / 2;  // Convert to distance in cm
  
  return distance;
}

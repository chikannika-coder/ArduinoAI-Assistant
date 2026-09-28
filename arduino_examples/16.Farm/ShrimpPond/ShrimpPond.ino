/*
  ShrimpPond  (ArduinoAI 2.5 หมวด 16 เกษตรอัจฉริยะ)
  โค้ดต้นฉบับจากโครงงานบ่อกุ้งอัจฉริยะ (ร.ร.สมบูรณ์ศาสน์ จ.ยะลา)
  งานอบรม ทสรช. 25-27 ก.ย. ที่ครูส่งมา (ไม่ได้แก้โค้ดด้านล่าง เก็บไว้เทียบ)

  จุดที่ควรแก้ (แก้แล้วในไฟล์ ShrimpPond.py):
   - เทียบค่า DO เป็นโวลต์กับ 5 เป็นจริงเกือบตลอด เครื่องตีน้ำจึงเปิดทั้งวัน
   - ค่า pH ที่แสดงเป็นโวลต์ ยังไม่ได้แปลงเป็น pH
   - ประกาศขาอัลตราโซนิกแต่ไม่ได้ใช้
*/

#include <OneWire.h>
#include <DallasTemperature.h>
#include <Servo.h>

// Define sensor pins
#define ONE_WIRE_BUS 2
#define PH_SENSOR_PIN A0
#define DO_SENSOR_PIN A1
#define ULTRASONIC_TRIG_PIN 3
#define ULTRASONIC_ECHO_PIN 4
#define AERATOR_RELAY_PIN 5
#define FEEDER_SERVO_PIN 6

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);
Servo feederServo;

void setup() {
  Serial.begin(9600);
  sensors.begin();
  feederServo.attach(FEEDER_SERVO_PIN);
  pinMode(AERATOR_RELAY_PIN, OUTPUT);
}

void loop() {
  // Read temperature
  sensors.requestTemperatures();
  float temperature = sensors.getTempCByIndex(0);

  // Read pH level
  float pH = analogRead(PH_SENSOR_PIN) * (5.0 / 1023.0);  // May need calibration

  // Read DO level (simplified, may need specific sensor calibration)
  float DO = analogRead(DO_SENSOR_PIN) * (5.0 / 1023.0);

  // Control aerator based on DO level
  if (DO < 5) {  // Example threshold
    digitalWrite(AERATOR_RELAY_PIN, HIGH);
  } else {
    digitalWrite(AERATOR_RELAY_PIN, LOW);
  }

  // Automated feeding (e.g., feed every 6 hours)
  static unsigned long lastFeedTime = 0;
  if (millis() - lastFeedTime >= 21600000) {
    activateFeeder();
    lastFeedTime = millis();
  }

  // Display data on LCD or Serial Monitor
  Serial.print("Temperature: ");
  Serial.println(temperature);
  Serial.print("pH: ");
  Serial.println(pH);
  Serial.print("DO: ");
  Serial.println(DO);

  delay(5000);
}

void activateFeeder() {
  feederServo.write(90);
  delay(5000);
  feederServo.write(0);
}

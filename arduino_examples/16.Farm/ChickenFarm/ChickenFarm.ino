/*
  ChickenFarm  (ArduinoAI 2.5 หมวด 16 เกษตรอัจฉริยะ)
  โค้ดต้นฉบับจากโครงงานฟาร์มไก่อัจฉริยะ (ร.ร.สบเมยวิทยาคม จ.แม่ฮ่องสอน)
  งานอบรม ทสรช. 25-27 ก.ย. ที่ครูส่งมา (ไม่ได้แก้โค้ดด้านล่าง เก็บไว้เทียบ)

  จุดที่ควรแก้ (แก้แล้วในไฟล์ ChickenFarm.py):
   - if (hour() == 8) ให้อาหารซ้ำทุกรอบ loop ตลอดชั่วโมง 8 โมง
   - setTime() ตั้งเวลาเอง ไฟดับแล้วเวลาเพี้ยน
   - ประกาศขา PIR ไว้แต่ไม่ได้ใช้
*/

#include <Servo.h>
#include <DHT.h>
#include <TimeLib.h>

#define DHTPIN 2
#define FEEDER_SERVO_PIN 9
#define PIR_PIN 3
#define HEATER_RELAY_PIN 4
#define HUMIDIFIER_RELAY_PIN 5

DHT dht(DHTPIN, DHT22);
Servo feederServo;

void setup() {
  dht.begin();
  feederServo.attach(FEEDER_SERVO_PIN);
  
  pinMode(HEATER_RELAY_PIN, OUTPUT);
  pinMode(HUMIDIFIER_RELAY_PIN, OUTPUT);

  // Assuming you don't have a real-time clock module and are setting the time manually
  setTime(12, 0, 0, 22, 9, 2023);  // set time to 12:00:00, 22 September 2023
}

void loop() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  // Control environment
  if (temperature < 20) {  // Example threshold
    digitalWrite(HEATER_RELAY_PIN, HIGH);  // Activate heater
  } else {
    digitalWrite(HEATER_RELAY_PIN, LOW);  // Deactivate heater
  }

  if (humidity < 60) {  // Example threshold
    digitalWrite(HUMIDIFIER_RELAY_PIN, HIGH);  // Activate humidifier
  } else {
    digitalWrite(HUMIDIFIER_RELAY_PIN, LOW);  // Deactivate humidifier
  }

  // Feed chickens at specific times
  if (hour() == 8) {
    activateFeeder();
  }

  // ... other logic
  delay(1000);
}

void activateFeeder() {
  feederServo.write(90);  // Rotate to release food
  delay(5000);  // Wait for 5 seconds
  feederServo.write(0);  // Rotate back to original position
}

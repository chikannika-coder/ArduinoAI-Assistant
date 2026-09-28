/*
  Scarecrow  (ArduinoAI 2.5 หมวด 16 เกษตรอัจฉริยะ)
  โค้ดต้นฉบับจากโครงงานหุ่นไล่กาอัจฉริยะเพื่อช่วยเกษตรกร (ร.ร.ราชประชานุเคราะห์ 37 จ.กระบี่)
  งานอบรม ทสรช. 25-27 ก.ย. ที่ครูส่งมา (ไม่ได้แก้โค้ดด้านล่าง เก็บไว้เทียบ)

  จุดที่ควรแก้ (แก้แล้วในไฟล์ Scarecrow.py):
   - pulseIn ไม่กำหนดเวลารอ ถ้าไม่มีเสียงสะท้อนจะค้าง 1 วินาที
*/

// Define pins for various components
const int PIR_PIN = 2; // PIR sensor connected to digital pin 2
const int ULTRASONIC_TRIG_PIN = 3; // Ultrasonic sensor trigger pin
const int ULTRASONIC_ECHO_PIN = 4; // Ultrasonic sensor echo pin
const int BUZZER_PIN = 5; // Buzzer connected to digital pin 5
const int LED_PIN = 6; // LED connected to digital pin 6
const int SERVO_PIN = 7; // Servo motor connected to digital pin 7

#include <Servo.h> // Include servo library
Servo servo; // Define servo object

void setup() {
  pinMode(PIR_PIN, INPUT); 
  pinMode(ULTRASONIC_TRIG_PIN, OUTPUT);
  pinMode(ULTRASONIC_ECHO_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  servo.attach(SERVO_PIN);

  Serial.begin(9600); // For debugging purposes
}

void loop() {
  int pirState = digitalRead(PIR_PIN);

  if(pirState == HIGH) { // If motion is detected
    float distance = getDistance();
    Serial.print("Distance: "); Serial.println(distance); // Print distance for debugging
    if(distance < 50) { // If the object is closer than 50cm
      scareAway(); // Execute scare action
    }
  }
  delay(100); // Delay for a short period before checking again
}

float getDistance() {
  long duration;
  float distance;

  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(ULTRASONIC_TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);

  duration = pulseIn(ULTRASONIC_ECHO_PIN, HIGH);
  distance = (duration / 2) * 0.0344;

  return distance;
}

void scareAway() {
  digitalWrite(BUZZER_PIN, HIGH); // Sound buzzer
  digitalWrite(LED_PIN, HIGH); // Turn on LED
  servo.write(90); // Move servo to 90 degrees
  delay(1000); // Wait for a second
  digitalWrite(BUZZER_PIN, LOW); // Turn off buzzer
  digitalWrite(LED_PIN, LOW); // Turn off LED
  servo.write(0); // Reset servo position
}

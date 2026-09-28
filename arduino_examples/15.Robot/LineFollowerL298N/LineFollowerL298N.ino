/*
  LineFollowerL298N  (ArduinoAI 2.4)
  หุ่นยนต์เดินตามเส้นด้วยโมดูล TCRT5000 2 ตัว และไดรเวอร์มอเตอร์ L298N

  การต่อสาย (Arduino Uno):
    TCRT5000 ซ้าย DO -> D2, ขวา DO -> D3 (VCC -> 5V, GND -> GND)
    L298N: ENA -> D5, IN1 -> D7, IN2 -> D8, IN3 -> D9, IN4 -> D10, ENB -> D6
    ถอดจัมเปอร์ ENA/ENB ออก ถ่าน 6-9V ต่อขา 12V ของ L298N และต่อ GND ร่วมกับ Arduino

  This example code is in the public domain.
*/

const int LEFT_SENSOR = 2;
const int RIGHT_SENSOR = 3;
const int ENA = 5, IN1 = 7, IN2 = 8;     // มอเตอร์ซ้าย
const int ENB = 6, IN3 = 9, IN4 = 10;    // มอเตอร์ขวา
const int SPEED = 150;                   // 0-255
const int BLACK = HIGH;                  // โมดูลส่วนใหญ่ให้ HIGH เมื่ออยู่บนเส้นดำ

void motor(int en, int a, int b, int speed) {
  digitalWrite(a, speed > 0 ? HIGH : LOW);
  digitalWrite(b, speed < 0 ? HIGH : LOW);
  analogWrite(en, abs(speed));
}

void setup() {
  pinMode(LEFT_SENSOR, INPUT);
  pinMode(RIGHT_SENSOR, INPUT);
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT); pinMode(ENA, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT); pinMode(ENB, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  bool leftBlack = digitalRead(LEFT_SENSOR) == BLACK;
  bool rightBlack = digitalRead(RIGHT_SENSOR) == BLACK;
  if (!leftBlack && !rightBlack) {         // อยู่คร่อมเส้น: วิ่งตรง
    motor(ENA, IN1, IN2, SPEED);
    motor(ENB, IN3, IN4, SPEED);
  } else if (leftBlack && !rightBlack) {   // เลี้ยวซ้าย
    motor(ENA, IN1, IN2, 0);
    motor(ENB, IN3, IN4, SPEED);
  } else if (rightBlack && !leftBlack) {   // เลี้ยวขวา
    motor(ENA, IN1, IN2, SPEED);
    motor(ENB, IN3, IN4, 0);
  } else {                                  // เส้นดำทั้งสองข้าง: หยุด
    motor(ENA, IN1, IN2, 0);
    motor(ENB, IN3, IN4, 0);
  }
  delay(20);
}

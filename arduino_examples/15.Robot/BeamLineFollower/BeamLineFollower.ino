/*
  BeamLineFollower  (ArduinoAI 2.4)
  หุ่นยนต์บีมที่เขียนโปรแกรมได้: ใช้วงจรขับมอเตอร์เดิมของหุ่นบีม (1k -> BC337 -> BD679)
  แต่ให้ Arduino อ่านเซนเซอร์และตัดสินใจแทน

  การต่อสาย (Arduino Uno) ถอดถ่านก่อน:
    แผงเซนเซอร์: สายเขียว (+) -> 5V, สายเหลือง (−) -> GND
                 สายขาวซ้าย -> A0, สายขาวขวา -> A1 (ย้ายตัวต้านทานปรับค่าได้ไปแถวเดียวกับสายขาว)
    วงจรมอเตอร์: D5 -> แถว 10 ของวงจรล้อซ้าย, D6 -> แถว 10 ของวงจรล้อขวา
    GND ของ Arduino -> รางไฟลบของบอร์ดทดลอง

  This example code is in the public domain.
*/

const int LEFT_SENSOR = A0;
const int RIGHT_SENSOR = A1;
const int LEFT_MOTOR = 5;     // ขา PWM
const int RIGHT_MOTOR = 6;    // ขา PWM
const int THRESHOLD = 500;    // มากกว่านี้ = พื้นขาว (หาค่าด้วย BeamSensorRead)
const int SPEED = 180;        // 0-255

void setup() {
  pinMode(LEFT_MOTOR, OUTPUT);
  pinMode(RIGHT_MOTOR, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  int left = analogRead(LEFT_SENSOR);
  int right = analogRead(RIGHT_SENSOR);
  // เห็นพื้นขาว ล้อข้างนั้นหมุน เห็นเส้นดำ ล้อข้างนั้นหยุด (กฎเดียวกับหุ่นยนต์บีม)
  analogWrite(LEFT_MOTOR, left > THRESHOLD ? SPEED : 0);
  analogWrite(RIGHT_MOTOR, right > THRESHOLD ? SPEED : 0);
  Serial.print("left:");
  Serial.print(left);
  Serial.print(" right:");
  Serial.println(right);
  delay(20);
}

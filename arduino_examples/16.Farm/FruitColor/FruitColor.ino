/*
  FruitColor  (ArduinoAI 2.5 หมวด 16 เกษตรอัจฉริยะ)
  วัดสีผลไม้ด้วยเซนเซอร์สี TCS3200 / TCS230 เพื่อดูความสุก
  อ้างอิงแนวคิดจากโครงงาน ทสรช.: เครื่องตรวจวัดความสุกของผลไม้ด้วยเซนเซอร์วัดค่าสี (ร.ร.ราชประชานุเคราะห์ 53 จ.สกลนคร)

  จุดที่ควรแก้ในโค้ดต้นฉบับของโครงงาน:
   - Measure_the_ripeness_of_fruit.ino อ่าน TCS3200 ด้วย analogRead ซึ่งอ่านไม่ได้ ต้องวัดความกว้างพัลส์ด้วย pulseIn
   - lcd.print() ต่อกันทุกรอบโดยไม่ lcd.clear() / lcd.setCursor() ข้อความจะเลื่อนจนอ่านไม่ออก

  ต่อสาย (Arduino Uno): S0 -> D4, S1 -> D5, S2 -> D6, S3 -> D7, OUT -> D8, OE -> GND
  This example code is in the public domain.
*/

const int S0 = 4, S1 = 5, S2 = 6, S3 = 7, OUT_PIN = 8;
const float RIPE_RATIO = 1.2;   // สีแดงเด่นกว่าเขียวเกินกี่เท่าจึงถือว่าสุก

long readColor(int a, int b) {
  digitalWrite(S2, a);
  digitalWrite(S3, b);
  delay(20);
  long t = pulseIn(OUT_PIN, LOW, 100000);   // พัลส์สั้น = สีนั้นเข้ม
  return t > 0 ? t : 100000;
}

void setup() {
  pinMode(S0, OUTPUT); pinMode(S1, OUTPUT);
  pinMode(S2, OUTPUT); pinMode(S3, OUTPUT);
  pinMode(OUT_PIN, INPUT);
  digitalWrite(S0, HIGH);   // ความถี่ 20%
  digitalWrite(S1, LOW);
  Serial.begin(9600);
}

void loop() {
  long red = readColor(LOW, LOW);
  long green = readColor(HIGH, HIGH);
  long blue = readColor(LOW, HIGH);
  float ratio = (float)green / red;
  Serial.print("red:"); Serial.print(red);
  Serial.print(" green:"); Serial.print(green);
  Serial.print(" blue:"); Serial.print(blue);
  Serial.println(ratio > RIPE_RATIO ? "  -> สุก" : "  -> ยังไม่สุก");
  delay(300);
}

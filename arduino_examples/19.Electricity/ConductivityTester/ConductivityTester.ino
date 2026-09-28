/*
  ConductivityTester (ArduinoAI 2.7 หมวด 19 พื้นฐานไฟฟ้า)
  สายปลาย A -> 5V, สายปลาย B -> A0 และตัวต้านทาน 10k จาก A0 ลง GND, LED ที่ D13
  This example code is in the public domain.
*/
void setup() { pinMode(13, OUTPUT); Serial.begin(9600); }
void loop() {
  int conduct = analogRead(A0) * 100L / 1023;
  digitalWrite(13, conduct > 10 ? HIGH : LOW);
  Serial.print("conduct:"); Serial.print(conduct);
  if (conduct > 80) Serial.println(" ตัวนำที่ดี");
  else if (conduct > 10) Serial.println(" นำไฟได้บ้าง");
  else Serial.println(" ฉนวน");
  delay(200);
}

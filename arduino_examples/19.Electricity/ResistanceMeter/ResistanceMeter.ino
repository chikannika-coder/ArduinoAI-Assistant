/* ResistanceMeter (ArduinoAI 2.7) 5V -> Rx -> A0 -> 10k -> GND  This example code is in the public domain. */
void setup() { Serial.begin(9600); }
void loop() {
  float raw = analogRead(A0);
  if (raw < 5) Serial.println("ไม่มีไฟผ่าน");
  else { Serial.print("ohms:"); Serial.println(10000.0 * (1023 - raw) / raw, 0); }
  delay(300);
}

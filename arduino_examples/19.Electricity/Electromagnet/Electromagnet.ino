/* Electromagnet (ArduinoAI 2.7) ปุ่ม D2 -> GND, รีเลย์ D7 (Active LOW)  This example code is in the public domain. */
bool magnet = false, wasPressed = false; unsigned long onSince = 0;
void setup() { pinMode(2, INPUT_PULLUP); pinMode(7, OUTPUT); digitalWrite(7, HIGH); Serial.begin(9600); }
void loop() {
  bool pressed = digitalRead(2) == LOW;
  if (pressed && !wasPressed) { magnet = !magnet; onSince = millis(); }
  wasPressed = pressed;
  if (magnet && millis() - onSince > 20000UL) magnet = false;
  digitalWrite(7, magnet ? LOW : HIGH);
  Serial.print("magnet:"); Serial.println(magnet);
  delay(30);
}

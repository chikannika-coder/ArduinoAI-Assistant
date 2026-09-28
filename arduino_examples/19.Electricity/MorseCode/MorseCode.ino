/* MorseCode (ArduinoAI 2.7) LED D13 + buzzer D8 ส่ง SOS  This example code is in the public domain. */
const int LED = 13, BUZ = 8, UNIT = 200;
void mark(int units) { digitalWrite(LED, HIGH); digitalWrite(BUZ, HIGH); delay(units * UNIT);
                       digitalWrite(LED, LOW); digitalWrite(BUZ, LOW); delay(UNIT); }
void setup() { pinMode(LED, OUTPUT); pinMode(BUZ, OUTPUT); }
void loop() {
  for (int i = 0; i < 3; i++) mark(1);   // S ...
  delay(2 * UNIT);
  for (int i = 0; i < 3; i++) mark(3);   // O ---
  delay(2 * UNIT);
  for (int i = 0; i < 3; i++) mark(1);   // S ...
  delay(2000);
}

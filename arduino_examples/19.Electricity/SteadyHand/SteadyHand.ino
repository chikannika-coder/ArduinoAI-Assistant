/* SteadyHand (ArduinoAI 2.7) รางลวด -> D2, ห่วง -> GND, buzzer D8  This example code is in the public domain. */
int touches = 0; bool touching = false;
void setup() { pinMode(2, INPUT_PULLUP); pinMode(8, OUTPUT); Serial.begin(9600); }
void loop() {
  if (digitalRead(2) == LOW) { digitalWrite(8, HIGH); if (!touching) { touches++; touching = true; } }
  else { digitalWrite(8, LOW); touching = false; }
  Serial.print("touches:"); Serial.println(touches);
  delay(20);
}

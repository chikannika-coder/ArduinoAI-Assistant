/* AlarmSwitch (ArduinoAI 2.7) ลวดกันขโมย D2->GND, ไม้หนีบเตือนฝน D3->GND, ปุ่ม reset D4, buzzer D8, LED D13
   This example code is in the public domain. */
bool alarm = false;
void setup() { pinMode(2, INPUT_PULLUP); pinMode(3, INPUT_PULLUP); pinMode(4, INPUT_PULLUP);
               pinMode(8, OUTPUT); pinMode(13, OUTPUT); Serial.begin(9600); }
void loop() {
  if (digitalRead(2) == HIGH || digitalRead(3) == LOW) alarm = true;
  if (digitalRead(4) == LOW) alarm = false;
  bool on = alarm && (millis() / 250) % 2;
  digitalWrite(8, on); digitalWrite(13, on);
  Serial.print("alarm:"); Serial.println(alarm);
  delay(50);
}

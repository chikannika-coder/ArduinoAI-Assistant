/* CellVoltmeter (ArduinoAI 2.7) ทองแดง -> A0, สังกะสี -> GND  This example code is in the public domain. */
void setup() { Serial.begin(9600); }
void loop() {
  long total = 0;
  for (int i = 0; i < 20; i++) { total += analogRead(A0); delay(5); }
  Serial.print("volts:"); Serial.println(total / 20.0 * 5.0 / 1023, 3);
  delay(400);
}

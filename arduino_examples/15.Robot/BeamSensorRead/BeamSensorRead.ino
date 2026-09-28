/*
  BeamSensorRead  (ArduinoAI 2.4)
  อ่านค่าแผงเซนเซอร์อินฟราเรด 2 แผงของหุ่นยนต์บีม แล้วส่งค่าออก Serial Monitor / Serial Plotter

  การต่อสาย (Arduino Uno):
    สายเขียว (+)  -> 5V        สายเหลือง (−) -> GND
    สายขาว (OUT) ซ้าย -> A0    สายขาว (OUT) ขวา -> A1
    ตัวต้านทานปรับค่าได้ 50k ต่อระหว่างสายขาวกับ GND เหมือนในหุ่นบีม

  พื้นขาว = ค่าสูง, เส้นดำ = ค่าต่ำ  ค่ากึ่งกลางใช้เป็น THRESHOLD ในตัวอย่าง BeamLineFollower
  This example code is in the public domain.
*/

const int LEFT_SENSOR = A0;
const int RIGHT_SENSOR = A1;

void setup() {
  Serial.begin(9600);
}

void loop() {
  int left = analogRead(LEFT_SENSOR);
  int right = analogRead(RIGHT_SENSOR);
  Serial.print("left:");
  Serial.print(left);
  Serial.print(" right:");
  Serial.println(right);
  delay(100);
}

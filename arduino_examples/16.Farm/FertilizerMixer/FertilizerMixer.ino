/*
  FertilizerMixer  (ArduinoAI 2.5 หมวด 16 เกษตรอัจฉริยะ)
  โค้ดต้นฉบับจากโครงงานต้นแบบเครื่องจำลองการผสมปุ๋ยอัตโนมัติ Ai v.2 (ร.ร.วัดไผ่ดำ จ.สิงห์บุรี)
  งานอบรม ทสรช. 25-27 ก.ย. ที่ครูส่งมา (ไม่ได้แก้โค้ดด้านล่าง เก็บไว้เทียบ)

  จุดที่ควรแก้ (แก้แล้วในไฟล์ FertilizerMixer.py):
   - จอ LCD ใช้ขา 5, 4, 3, 2 ซ้ำกับ HX711 (4, 5) และปั๊ม (2, 3) อุปกรณ์จึงทำงานไม่ได้
   - scale.set_scale() ไม่ได้ใส่ค่าปรับเทียบ น้ำหนักที่ได้ยังไม่ใช่กรัม
   - ยังไม่มีขั้นตอนผสมปุ๋ย
*/

#include <HX711.h>
#include <LiquidCrystal.h>

#define LOADCELL_DOUT  4
#define LOADCELL_SCK   5
#define PUMP1_PIN      2
#define PUMP2_PIN      3

HX711 scale(LOADCELL_DOUT, LOADCELL_SCK);
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

void setup() {
  Serial.begin(9600);
  lcd.begin(16, 2);
  
  pinMode(PUMP1_PIN, OUTPUT);
  pinMode(PUMP2_PIN, OUTPUT);

  scale.set_scale();
  scale.tare();
}

void loop() {
  float weight = scale.get_units(5);  // Get weight data from the HX711
  lcd.setCursor(0, 0);
  lcd.print("Weight: ");
  lcd.print(weight);
  lcd.print(" g   ");  // Print weight to LCD
  
  // Your mixing logic here

  delay(500);
}

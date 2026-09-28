/*
  WeatherStation  (ArduinoAI 2.5 หมวด 16)
  สถานีวัดอากาศโรงเรียน: อุณหภูมิ ความชื้น (DHT22) แสง (LDR) และปริมาณน้ำฝน (ถังกระดก)

  ต่อสาย (Arduino Uno): DHT22 DATA -> D4, LDR (โมดูล AO) -> A0,
  เครื่องวัดน้ำฝน: สายหนึ่ง -> D2 (ขาอินเทอร์รัปต์), อีกสาย -> GND
  ต้องติดตั้งไลบรารี "DHT sensor library" ของ Adafruit
  This example code is in the public domain.
*/
#include <DHT.h>

const int RAIN_PIN = 2;
const int LIGHT_PIN = A0;
const float MM_PER_TIP = 0.2;   // ดูในคู่มือเครื่องวัดน้ำฝน
DHT dht(4, DHT22);

volatile unsigned long tips = 0;
volatile unsigned long lastTip = 0;

void onTip() {
  unsigned long now = millis();
  if (now - lastTip > 200) {    // ไม่นับซ้ำ (สวิตช์เด้ง)
    tips++;
    lastTip = now;
  }
}

void setup() {
  pinMode(RAIN_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(RAIN_PIN), onTip, FALLING);
  dht.begin();
  Serial.begin(9600);
}

void loop() {
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  if (isnan(t) || isnan(h)) {
    Serial.println("อ่าน DHT22 ไม่ได้");
  } else {
    Serial.print("temp_c:"); Serial.print(t);
    Serial.print(" humidity:"); Serial.print(h);
  }
  Serial.print(" light:"); Serial.print(analogRead(LIGHT_PIN) * 100L / 1023);
  noInterrupts();
  unsigned long n = tips;
  interrupts();
  Serial.print(" rain_mm:"); Serial.println(n * MM_PER_TIP);
  delay(5000);
}

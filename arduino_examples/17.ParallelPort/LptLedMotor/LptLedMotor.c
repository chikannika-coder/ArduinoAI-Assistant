/*
  LptLedMotor  (ArduinoAI 2.5 หมวด 17 จาก Turbo C พอร์ตขนาน สู่ MicroPython)
  โค้ด Turbo C เดิมของครู: testoutportLed.c / testoutportMotor.c (โฟลเดอร์ codeExamOutport)
  เปิด LED หรือมอเตอร์ที่ขา D0 จนกว่าจะกดแป้นพิมพ์
  โปรแกรมนี้รันบน DOS (Turbo C 2.0/3.0) คุมฮาร์ดแวร์ผ่านพอร์ตขนาน LPT1: 0x378 = ขาข้อมูล D0-D7, 0x379 = ขาสถานะ S3-S7
  ไฟล์ .py ในโฟลเดอร์เดียวกันคือโค้ดเดียวกันที่แปลงเป็น MicroPython
*/

#include <stdio.h>
main()
{
	outport(0x378,01); /*Led on of motor on*/
	do{
	
	}while(!kbhit());
	outport(0x378,0);/*Led off or motor off*/
	
}
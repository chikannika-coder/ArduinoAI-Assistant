/*
  LptSensorMotor  (ArduinoAI 2.5 หมวด 17 จาก Turbo C พอร์ตขนาน สู่ MicroPython)
  โค้ด Turbo C เดิมของครู: IR_M.C และ LDR_M.C (โฟลเดอร์ codeExamOutport)
  อ่านเซนเซอร์ที่ขา S4 แล้วสั่งมอเตอร์ที่ขา D0 (ไฟล์ LDR_M.C เหมือนกันแต่สลับเปิด/ปิด)
  โปรแกรมนี้รันบน DOS (Turbo C 2.0/3.0) คุมฮาร์ดแวร์ผ่านพอร์ตขนาน LPT1: 0x378 = ขาข้อมูล D0-D7, 0x379 = ขาสถานะ S3-S7
  ไฟล์ .py ในโฟลเดอร์เดียวกันคือโค้ดเดียวกันที่แปลงเป็น MicroPython
*/

#include <stdio.h>
main()
{ char indata;

 do{
  indata = inport(0x379);
  gotoxy(6,6);
  printf(" INPUT S4: [ %s ]",((indata&0x10)==0x10)? "OFF":"ON");

  if((indata&0x10) == 0x10)   /* if true senser received */
   outport(0x378,0);    /* on motor */
  else
   outport(0x378,1);   /* off motor */

 }while(!kbhit());
 outport(0x378,0);
}
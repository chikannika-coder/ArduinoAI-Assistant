/*
  LptDuty  (ArduinoAI 2.5 หมวด 17 จาก Turbo C พอร์ตขนาน สู่ MicroPython)
  โค้ด Turbo C เดิมของครู: testoutport2_duty.c (โฟลเดอร์ codeExamOutport)
  ปรับความสว่าง/ความเร็วด้วยการเปิด-ปิดเป็นจังหวะ กด + / - เพื่อปรับ duty
  โปรแกรมนี้รันบน DOS (Turbo C 2.0/3.0) คุมฮาร์ดแวร์ผ่านพอร์ตขนาน LPT1: 0x378 = ขาข้อมูล D0-D7, 0x379 = ขาสถานะ S3-S7
  ไฟล์ .py ในโฟลเดอร์เดียวกันคือโค้ดเดียวกันที่แปลงเป็น MicroPython
*/

#include <stdio.h>
main()
{	int duty=0;	/*value 0 ~ 100*/
	char ch;
	do{
		 outport(0x378,1);
		 delay(duty);
		 outport(0x378,0);
		 delay(100-duty);
		 if(kbhit())
		 {
			ch=getch();
			if(ch == '+')
			  duty++;
			if(ch == '-')
			 duty--;

			if(duty>100)
			   duty=100;
			else
			if(duty < 0)
			   duty=0;
		 }
		 gotoxy(6,6);
		 printf("duty= [ %d ] ",duty);
	}while(ch!= 27);
	outport(0x378,0);
}
/*
  WaterTurbidity  (ArduinoAI 2.5 หมวด 17 จาก Turbo C พอร์ตขนาน สู่ MicroPython)
  โค้ด Turbo C เดิมของครู: Project/Water-Fail/WATER.C
  ตรวจน้ำใส/น้ำขุ่นที่ขา S5 แล้วเปิดปั๊มที่ขา D0
  โปรแกรมนี้รันบน DOS (Turbo C 2.0/3.0) คุมฮาร์ดแวร์ผ่านพอร์ตขนาน LPT1: 0x378 = ขาข้อมูล D0-D7, 0x379 = ขาสถานะ S3-S7
  ไฟล์ .py ในโฟลเดอร์เดียวกันคือโค้ดเดียวกันที่แปลงเป็น MicroPython
*/

#include<stdio.h>
#include<conio.h>
#include<string.h>
#include<stdlib.h>
#include<graphics.h>

#define UPCURCOR 72
#define DOWNCURCOR 80
#define ENTER 13

void Open_Graph( char *dir);
void Windows(int x1, int y1, int x2, int y2, char *texttitle);
void Button(int x1, int y1, int x2 ,int y2, int active, int select);
void Line3d(int x1, int y1, int x2, int y2);
void Textbox(int x1, int y1, int x2, int y2, int colorbg);
void Groupbox(int x1, int y1, int x2, int y2, char *text);
void Status_bar(int x1, int y1, int x2, int y2, char *txtstatus);
int Caltextlength( char *txt );
void Label(int x1, int y1, int x2, int y2, int color, char *text);
void Main_Menu();
void Select_Menu();
void Water_effect();
void Display();
void Control();
void Read_Sensor();

int StartP = 0;    // 1 to start program
int Choice = 0;    // ( 1-3 ) for choice
int WATER = 0;     // 0 for NUM-SAI , 1 for NUM-KHUN
int ExitLoop = 0;

int main(void)
{
	Open_Graph("../bgi/");
	Main_Menu();
	return 0;
}

void Read_Sensor()
{
	if( (inportb(0x379)&32) == 32 )
		WATER = 1;
	else
		WATER = 0;
}

void Water_effect()
{
		int x,y,r,i;
		randomize();
		for( i=0 ; i<400 ; i++)
		{
	 x = random(260) + 70;
	 y = random(205) + 90;
	 r = random(2)+1;
	 setcolor(BLACK);
	 circle(x,y,r);
	 setfillstyle(1,BLACK);
	 floodfill(x,y,BLACK);
		}
}

void Control()
{
///////////////////////////////////////////////////////////
	if( StartP == 1 ) {
		Read_Sensor();
		if( WATER == 1 ) {
			outport(0x378,1);
			do
			{
				Read_Sensor();
				Display();
			}while( (!kbhit()) && (WATER == 1) );
			Display();
		}
		else {
			outport(0x378,0);
		}
	}
	else
		outport(0x378,0);
//////////////////////////////////////////////////////////
}

void Display()
{

	if( !StartP )
	{
		Textbox(50,80,340,300,LIGHTBLUE);
		Textbox(50,340,340,420,WHITE);
		setcolor(BLACK);
		settextstyle(1,0,5);
		outtextxy(135,350,"STOP");
	}else{
		if( WATER )
		{
			Textbox(50,80,340,300,BLUE);
			Water_effect();
			Textbox(50,340,340,420,WHITE);
			setcolor(RED);
			settextstyle(1,0,5);
			outtextxy(120,350,"ALERT!");
		}else{
			Textbox(50,80,340,300,LIGHTBLUE);
			Textbox(50,340,340,420,WHITE);
			setcolor(GREEN);
			settextstyle(1,0,5);
			outtextxy(120,350,"NORMAL");
		}
	}
}
void Select_Menu()
{
	char ch;
	do{
		ch = 0;
		Control();
		if ( kbhit() ) ch = getch();
		if( ch != 0 )
		{
			if( ch == DOWNCURCOR )
			{
				Choice++;
				if( Choice == 3 ) Choice = 0;
			}
			if( ch == UPCURCOR )
			{
				Choice--;
				if( Choice == -1 ) Choice = 2;
			}

			if( Choice == 0 )
			{
				Button(400,270,600,310,0,1);
				Button(400,320,600,360,0,0);
				Button(400,370,600,410,0,0);

			}else
			if( Choice == 1 )
			{
				Button(400,270,600,310,0,0);
				Button(400,320,600,360,0,1);
				Button(400,370,600,410,0,0);
			}
			else if( Choice == 2 )
			{
				Button(400,270,600,310,0,0);
				Button(400,320,600,360,0,0);
				Button(400,370,600,410,0,1);
			}
			setcolor(BLACK);
			settextstyle(2,0,4);
			outtextxy(460,285,"Start Control");
			outtextxy(460,335,"Stop Control");
			outtextxy(460,385,"Exit Program");
		}


	}while( ch != ENTER );
	if( Choice == 0 ) StartP = 1;
	else StartP = 0;

}

void Main_Menu()
{
	Windows(1,1,639,479,"Test");
	Groupbox(15,40,370,440,"Display");
	Groupbox(380,40,625,230,"Status");
	Button(400,270,600,310,0,1);
	Button(400,320,600,360,0,0);
	Button(400,370,600,410,0,0);
	setcolor(BLACK);
	outtextxy(460,285,"Start Control");
	outtextxy(460,335,"Stop Control");
	outtextxy(460,385,"Exit Program");
	do{
		Display();
		Select_Menu();

	}while( Choice != 2 );
}

// ------------- Open Graphics ----------------------

void Open_Graph( char *dir )
{
	int Gd = DETECT, Gm;
	initgraph( &Gd, &Gm , dir);
}

// ------------- Create Windows ----------------------
void Windows( int x1, int y1 , int x2 , int y2, char *texttitle)
{
	setlinestyle(0,0,1);
	setcolor(WHITE);
	line(x1,y1,x1,y2);
	line(x1,y1,x2,y1);
	setcolor(LIGHTGRAY);
	line(x1+1,y1+1,x1+1,y2);
	line(x1+1,y1+1,x2,y1+1);
	setcolor(BLACK);
	line(x2,y1,x2,y2);
	line(x1,y2,x2,y2);
	setcolor(DARKGRAY);
	line(x2-1,y1+1,x2-1,y2-1);
	line(x1+1,y2-1,x2-1,y2-1);
	setfillstyle(1,LIGHTGRAY);
	bar(x1+2,y1+2,x2-2,y2-2);
	setfillstyle(1, BLUE);
	bar(x1+3,y1+3,x2-3,y1+17);
	Line3d(x1+3,y1+19,x2-3,y1+19);
	Button(x1+5,y1+4,x1+15,y1+14,0,0);
	settextstyle(2,0,4);
	setcolor(WHITE);
	outtextxy(x1+19,y1+3,texttitle);

}

// --------------------- Create Statusbar-----------------------
void Status_bar(int x1, int y1, int x2, int y2, char *txtstatus)
{
	int lentxt = Caltextlength(txtstatus);
	Button(x1,y1,x2,y2,0,0);
	settextstyle(2,0,4);
	setcolor(BLACK);
	outtextxy(x2-lentxt,y1+2,txtstatus);
}

// ---------------------- Create Label-------------------------
void Label(int x1, int y1, int x2, int y2, int color, char *text)
{
	int Lengthtext = 0;
	int i, j, x ,y;
	char strtmp[100];
	i = j = 0;
	x = x1;
	y = y1+10;

	setfillstyle(1,color);
	bar(x1,y1,x2,y2);
	settextstyle(2,0,4);
	setcolor(BLACK);
	do{
		if( text[i] != '\n')
		{
			strtmp[j] = text[i];
			j++;
			Lengthtext += 6;
		}
		if( Lengthtext > (x2 - x1) || text[i] == '\n')
		{
			strtmp[j] = '\0';
			outtextxy(x+5,y,strtmp);
			y += 15;
			j = 0;
			Lengthtext = 0;
		}
		i++;

	}while( i < strlen(text) );
	strtmp[j] = '\0';
	outtextxy(x+5,y,strtmp);


}

// ------------------------Create Button---------------------
void Button(int x1, int y1, int x2,int y2 , int active , int select)
{
	if( active )
	{
		setlinestyle(0,0,1);
		setcolor(BLACK);
		line(x1,y1,x1,y2);
		line(x1,y1,x2,y1);
		setcolor(DARKGRAY);
		line(x1+1,y1+1,x1+1,y2);
		line(x1+1,y1+1,x2,y1+1);
		setcolor(WHITE);
		line(x2,y1,x2,y2);
		line(x1,y2,x2,y2);
		setcolor(LIGHTGRAY);
		line(x2-1,y1+1,x2-1,y2-1);
		line(x1+1,y2-1,x2-1,y2-1);
		setfillstyle(1,LIGHTGRAY);
		bar(x1+2,y1+2,x2-2,y2-2);

	}else{
		setlinestyle(0,0,1);
		setcolor(WHITE);
		line(x1,y1,x1,y2);
		line(x1,y1,x2,y1);
		setcolor(LIGHTGRAY);
		line(x1+1,y1+1,x1+1,y2);
		line(x1+1,y1+1,x2,y1+1);
		setcolor(BLACK);
		line(x2,y1,x2,y2);
		line(x1,y2,x2,y2);
		setcolor(DARKGRAY);
		line(x2-1,y1+1,x2-1,y2-1);
		line(x1+1,y2-1,x2-1,y2-1);
		setfillstyle(1,LIGHTGRAY);
		bar(x1+2,y1+2,x2-2,y2-2);
	}
	if( select )
	{
		setlinestyle(1,0,1);
		setcolor(DARKGRAY);
		rectangle(x1+4,y1+4,x2-4,y2-4);
	}
}

// ---------------------- Create Line---------------------
void Line3d(int x1, int y1, int x2, int y2)
{
	setlinestyle(0,0,1);
	setcolor(DARKGRAY);
	line(x1,y1,x2,y2);
	setcolor(WHITE);
	line(x1+1,y1+1,x2+1,y2+1);
}


// -----------------------Create Text box-----------------
void Textbox(int x1, int y1, int x2, int y2, int colorbg)
{
	setlinestyle(0,0,1);
	setcolor(BLACK);
	line(x1,y1,x1,y2);
	line(x1,y1,x2,y1);
	setcolor(DARKGRAY);
	line(x1+1,y1+1,x1+1,y2);
	line(x1+1,y1+1,x2,y1+1);
	setcolor(WHITE);
	line(x2,y1,x2,y2);
	line(x1,y2,x2,y2);
	setcolor(LIGHTGRAY);
	line(x2-1,y1+1,x2-1,y2-1);
	line(x1+1,y2-1,x2-1,y2-1);
	setfillstyle(1,LIGHTGRAY);
	bar(x1+2,y1+2,x2-2,y2-2);
	setfillstyle(1,colorbg);
	bar(x1+2,y1+2,x2-2,y2-2);
}

// ------------------------Create Group box----------------
void Groupbox(int x1, int y1, int x2, int y2, char *text)
{
	int lengthtext = Caltextlength(text);
	Line3d(x1,y1,x1+5,y1);             // --
	Line3d(x1+11+lengthtext,y1,x2,y1);  //    ------
	Line3d(x1,y1,x1,y2);               // |
	Line3d(x1,y2,x2,y2);               // ---------
	Line3d(x2,y1,x2,y2);               //         |
	settextstyle(2,0,4);
	setcolor(BLACK);
	outtextxy(x1+10,y1-7,text);
}

int Caltextlength( char *txt )
{
	int i, lengthtext = 0;
	for( i=0 ; i<strlen(txt) ; i++ )
		lengthtext += 6;
	return lengthtext;
}




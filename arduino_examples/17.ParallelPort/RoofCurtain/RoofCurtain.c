/*
  RoofCurtain  (ArduinoAI 2.5 หมวด 17 จาก Turbo C พอร์ตขนาน สู่ MicroPython)
  โค้ด Turbo C เดิมของครู: Project/Roof/RoofAndCurtain.C
  หลังคาและม่านอัตโนมัติ: ฝนตกปิดหลังคา แดดจ้าปิดม่าน ใช้สเต็ปมอเตอร์ 2 ตัว
  โปรแกรมนี้รันบน DOS (Turbo C 2.0/3.0) คุมฮาร์ดแวร์ผ่านพอร์ตขนาน LPT1: 0x378 = ขาข้อมูล D0-D7, 0x379 = ขาสถานะ S3-S7
  ไฟล์ .py ในโฟลเดอร์เดียวกันคือโค้ดเดียวกันที่แปลงเป็น MicroPython
*/

#include<stdio.h>
#include<graphics.h>
#include<conio.h>

#define ACTIVE 1
#define SELECT 1
#define OPEN 1
#define CLOSE 0
#define TRUE 1
#define FALSE 0
#define DELAY 3

// Graphic Function
void Open_Graph( char *dir);
void windows(int x1, int y1, int x2, int y2, char *texttitle);
void button(int x1, int y1, int x2 ,int y2, int active, int select);
void line3d(int x1, int y1, int x2, int y2);
void textbox(int x1, int y1, int x2, int y2, int colorbg);
void groupbox(int x1, int y1, int x2, int y2, char *text);
void status_bar(int x1, int y1, int x2, int y2, char *txtstatus);
void label(int x1, int y1, int x2, int y2, int color, char *text);
int Caltextlength( char *txt );
int Main_Menu( int LastChooice );
void ShowChoice( int Choice , int actice );
int Menu_Exit( void );
void Display();

// Control Function
void Manual_Control( void );
void StartStop_Control( void );
void Autometic_Control( void );
int CheckRain( void );
int CheckSunny( void );
void DriveCurtain(int);
void DriveRoof(int);
int EvantHanding(void);
void OutportCenter(void);
int Status_Curtain(void);
int Inport_(void);

// gobal variable
int Before;
int Status_Roof = OPEN;// Standby Value
int ROOF = 0;
int CURTAIN = 0;
int STATUS = 0;

int main(void)
{
	int Choice = 0;
	int Done = 0;
	Open_Graph("../BGI/");
	do{
		Choice = Main_Menu(Choice);
		switch( Choice )
		{
			case 0 : StartStop_Control(); break;
			case 1 : Manual_Control(); break;
			case 3 : Done = Menu_Exit(); break;
		}

	}while( Done != 1 );
	closegraph();
	return 0;
}

int Inport_(void)
{
	int i, in, in_x, in_y, cX = 0, cY = 0;
	in_x = inportb(0x379);
	while( (cX < 900) && (cY < 900) )
	{
		cX = 0; cY = 0;
		for( i = 0; i < 1000; i++)
		{
			in = inportb(0x379);
			if( in == in_x )
				cX++;
			else
			{
				if( cY == 0 ) in_y = in;
				cY++;
			}
		}
	}
	if( cX > cY ) return in_x;
	else return in_y;
}

int Status_Curtain(void)
{
	int i = Inport_();

	if( (i & 128) == 128 ) return 1; // OPEN COMPLETE
	else if( (i & 64) == 0 ) return -1; // CLOSE COMPLETE
	else return 0; // OPENNING OR CLOSING
}

void OutportCenter(void)
{
	int Sunny, Status, Rain;
	// Check Balance Of Sensor Sunny with Curtain
	Sunny = CheckSunny();
	Status = Status_Curtain();
	if( (Sunny == 1) && (Status != -1) )
		DriveCurtain(CLOSE);
	else if( (Sunny == 0) && (Status != 1) )
		DriveCurtain(OPEN);

	// Check Balance Of Sensor Rain with Roof
	Rain = CheckRain();
	if( (Rain == 1) && (Status_Roof == OPEN) )
		DriveRoof(CLOSE);
	else if( (Rain == 0) && (Status_Roof == CLOSE) )
		DriveRoof(OPEN);
}

int EvantHanding(void)
{
	char ch, i;
	if( kbhit() ) {
		ch = getch();
		if( ch == 27 )  return -1; // EXIT PROGRAM
	}
	i = Inport_();
	if( Before != i )
	{
		Before = i;
		return 1;
	}
	else
		return 0;
}

int ObjectBalance(void)
{
	// Case 1 : Sunny But Window OPEN = FALSE
	if( CheckSunny() && Status_Curtain() != -1 ) return FALSE;
	// Case 2 : Darkness But Window CLOSE = FALSE
	if( !CheckSunny() && Status_Curtain() != 1 ) return FALSE;
	// Case 3 : Rainning But Roof OPEN = FALSE
	if( CheckRain() && (Status_Roof == OPEN) ) return FALSE;
	// Case 4 : Not Have Rain But Roof CLOSE = FALSE
	if( !CheckRain() && (Status_Roof == CLOSE) ) return FALSE;
	// else
	return TRUE; // object balance
}

void DriveCurtain( int Status)
{
	static int step = 0;
	int Step_Curtain[4] = { 1, 2, 4, 8};

	if( Status == OPEN )
	{
		while( Status_Curtain() != 1 )
		{
			outport( 0x378, Step_Curtain[step++]);
			if( step == 4 ) step = 0;
			delay(DELAY);
		}
	}
	else
	{
		while( Status_Curtain() != -1 )
		{
			outport( 0x378, Step_Curtain[step--]);
			if( step == -1 ) step = 3;
			delay(DELAY);
		}
	}
}

void DriveRoof( int Status)
{
	static int step2 = 0;
	int Step_Roof[4] = { 16+32, 32+64, 64+128, 128+16};
	int TRoof;

	if( Status == OPEN )
	{
		TRoof = 0;
		while( TRoof++ < 1000 )
		{
			outport( 0x378,Step_Roof[step2++]);
			if( step2 > 3 ) step2 = 0;
			delay(2*DELAY);
		}
		Status_Roof = OPEN;
	}
	else
	{ // CLOSE
		TRoof = 1000;
		while( TRoof > 0 )
		{
			outport( 0x378,Step_Roof[step2--]);
			if( step2 < 0 ) step2 = 3;
			delay(DELAY);
			TRoof--;
		}
		Status_Roof = CLOSE;
	}
}

int CheckRain(void)
{
	// BIT 5 of 0x379
	if( (Inport_() & 32) == 32 )
		return TRUE; // Rainning
	else
		return FALSE; // Not Have Rain
}

int CheckSunny(void)
{
	// BIT 4 of 0x379
	if( (Inport_() & 16) == 0 )
		return TRUE; // Sunny
	else
		return FALSE; // Darkness
}

void Open_Graph( char *dir )
{
	int Gd = DETECT, Gm;
	initgraph( &Gd, &Gm , dir);
}

void windows( int x1, int y1 , int x2 , int y2, char *texttitle)
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
	line3d(x1+3,y1+19,x2-3,y1+19);
	button(x1+5,y1+4,x1+15,y1+14,0,0);
	settextstyle(2,0,4);
	setcolor(WHITE);
	outtextxy(x1+19,y1+3,texttitle);

}

void status_bar(int x1, int y1, int x2, int y2, char *txtstatus)
{
	int lentxt = Caltextlength(txtstatus);
	button(x1,y1,x2,y2,0,0);
	settextstyle(2,0,4);
	setcolor(BLACK);
	outtextxy(x2-lentxt,y1+2,txtstatus);
}


void button(int x1, int y1, int x2,int y2 , int active , int select)
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

void line3d(int x1, int y1, int x2, int y2)
{
	setlinestyle(0,0,1);
	setcolor(DARKGRAY);
	line(x1,y1,x2,y2);
	setcolor(WHITE);
	line(x1+1,y1+1,x2+1,y2+1);
}

void textbox(int x1, int y1, int x2, int y2, int colorbg)
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

void groupbox(int x1, int y1, int x2, int y2, char *text)
{
	int lengthtext = Caltextlength(text);
	line3d(x1,y1,x1+5,y1);             // --
	line3d(x1+11+lengthtext,y1,x2,y1);  //    ------
	line3d(x1,y1,x1,y2);               // |
	line3d(x1,y2,x2,y2);               // ---------
	line3d(x2,y1,x2,y2);               //         |
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


int Main_Menu( int LastChoice )
{
	int Evant;
	char ch = 0;
	int Choice = LastChoice;
	int tmp1,tmp2,tmp3,tmp4;

	windows(1,1,639,479,"Test Title");
	status_bar(1,460,639,480,"[^] [v] and [Enter] to select menu.");
	groupbox(30,50,440,440,"Display");
	textbox(40,60,430,430,BLACK);
	Display();
	ShowChoice( Choice , !ACTIVE);

	// 72 = up      80 = down   75 = left   77 = right
	do{
		tmp1 = CURTAIN;
		tmp3 = ROOF;
		do{
			tmp2 = CURTAIN;
			tmp4 = ROOF;
			if( tmp1 != tmp2  || tmp3 != tmp4)
				Display();
			ch = 0;
			ch = getch();
		}while( ch != 13 && ch != 72 && ch != 80 );

		if( ch != 13 )
		{
			switch(ch)
			{
				case 72 : Choice--; break;
				case 80 : Choice++; break;
			}
			if( Choice == -1 ) Choice = 3;
			if( Choice == 4 ) Choice = 0;
			ShowChoice(Choice,0);
		}

	}while( ch != 13 ); // Loop until Enter
	ShowChoice(Choice,1);
	delay(300);
	return Choice;
}

void ShowChoice( int Choice , int active )
{

	switch( Choice )
	{
		case 0 : {
			button(460,70,600,120,active,SELECT);
			button(460,130,600,180,!ACTIVE,!SELECT);
			button(460,190,600,240,!ACTIVE,!SELECT);
			button(460,250,600,300,!ACTIVE,!SELECT);
			settextstyle(2,0,4);
			setcolor(BLACK);
			if( STATUS )
				outtextxy(495,90,"Stop Control");
			else
				outtextxy(495,90,"Start Control");
			outtextxy(490,150,"Manual Control");
			outtextxy(515,210,"About");
			outtextxy(520,270,"Exit");
		}break;
		case 1 : {
			button(460,70,600,120,!ACTIVE,!SELECT);
			button(460,130,600,180,active,SELECT);
			button(460,190,600,240,!ACTIVE,!SELECT);
			button(460,250,600,300,!ACTIVE,!SELECT);
			settextstyle(2,0,4);
			setcolor(BLACK);
			if( STATUS )
				outtextxy(495,90,"Stop Control");
			else
				outtextxy(495,90,"Start Control");
			outtextxy(490,150,"Manual Control");
			outtextxy(515,210,"About");
			outtextxy(520,270,"Exit");
		}break;
		case 2 : {
			button(460,70,600,120,!ACTIVE,!SELECT);
			button(460,130,600,180,!ACTIVE,!SELECT);
			button(460,190,600,240,active,SELECT);
			button(460,250,600,300,!ACTIVE,!SELECT);
			settextstyle(2,0,4);
			setcolor(BLACK);
			if( STATUS )
				outtextxy(495,90,"Stop Control");
			else
				outtextxy(495,90,"Start Control");
			outtextxy(490,150,"Manual Control");
			outtextxy(515,210,"About");
			outtextxy(520,270,"Exit");
		}break;
		case 3 : {
			button(460,70,600,120,!ACTIVE,!SELECT);
			button(460,130,600,180,!ACTIVE,!SELECT);
			button(460,190,600,240,!ACTIVE,!SELECT);
			button(460,250,600,300,active,SELECT);
			settextstyle(2,0,4);
			setcolor(BLACK);
			if( STATUS )
				outtextxy(495,90,"Stop Control");
			else
				outtextxy(495,90,"Start Control");
			outtextxy(490,150,"Manual Control");
			outtextxy(515,210,"About");
			outtextxy(520,270,"Exit");
		}break;
	}
}


int Menu_Exit( void )
{
	char ch = 0;
	int choice1 = 0,choice2 = 1;
	windows(190,140,450,300,"Exit");
	settextstyle(2,0,4);
	setcolor(BLACK);
	outtextxy(240,190,"Do you want to exit program?");
	button(250,230,310,255,0,choice1);
	button(330,230,390,255,0,choice2);
	settextstyle(2,0,4);
	setcolor(BLACK);
	outtextxy(343,237,"  OK");
	outtextxy(258,237," Cancel");
	do{
		do{
			ch = getch();
		}while(ch != 75 && ch != 77 && ch != 13);
		// While press left ,right or enter key.
		if( ch != 13 )
		{
			if( choice1 == 1 )
			{
				choice1 = 0;
				choice2 = 1;
			}else{
				choice1 = 1;
				choice2 = 0;
			}
			button(250,230,310,255,0,choice1);
			button(330,230,390,255,0,choice2);
			settextstyle(2,0,4);
			setcolor(BLACK);
			outtextxy(343,237,"  OK");
			outtextxy(258,237," Cancel");
		}
	}while( ch != 13 );
	if(choice1 == 1)
	{
		button(250,230,310,255,1,choice1);
		settextstyle(2,0,4);
		setcolor(BLACK);
		outtextxy(343,237,"  OK");
		outtextxy(258,237," Cancel");
		delay(300);
		return 0;
	}else{
		button(330,230,390,255,1,choice2);
		settextstyle(2,0,4);
		setcolor(BLACK);
		outtextxy(343,237,"  OK");
		outtextxy(258,237," Cancel");
		delay(300);
		return 1;  // Exit
	}
}

void Manual_Control()
{
	int Choice1 = 1, Choice2 = 0;
	char ch = 0;

	STATUS = 0;
	windows(150,100,490,380,"Manual control");
	groupbox(170,140,470,300,"Control");
	button(200,180,440,210,!ACTIVE,Choice1); // roof button
	button(200,230,440,260,!ACTIVE,Choice2); // curtain button
	button(350,310,450,370,!ACTIVE,0); // exit button
	settextstyle(2,0,4);
	setcolor(BLACK);
	outtextxy(180,320,"[^] [v] to select menu");
	outtextxy(365,335,"[ESC] to exit");
	if( ROOF )
		outtextxy(260,190,"[Enter] to close roof");
	else
		outtextxy(260,190,"[Enter] to open roof");

	if( CURTAIN )
		outtextxy(260,240,"[Enter] to close curtain");
	else
		outtextxy(260,240,"[Enter] to open curtain");

	do{
		do{
			ch = getch();
		}while( ch != 72 && ch != 80 && ch != 27 && ch != 13 );

		if( ch == 72 || ch == 80 ) // up and down
		{
			if( Choice1 == 1 )
			{
				Choice1 = 0;
				Choice2 = 1;

			}else{
				Choice1 = 1;
				Choice2 = 0;
			}
			button(200,180,440,210,!ACTIVE,Choice1); // roof button
			button(200,230,440,260,!ACTIVE,Choice2); // curtain button
			settextstyle(2,0,4);
			setcolor(BLACK);
			if( ROOF )
				outtextxy(260,190,"[Enter] to close roof");
			else
				outtextxy(260,190,"[Enter] to open roof");

			if( CURTAIN )
				outtextxy(260,240,"[Enter] to close curtain");
			else
				outtextxy(260,240,"[Enter] to open curtain");

		}
		if( ch == 13 )
		{
			button(200,180,440,210,Choice1,Choice1); // roof button
			button(200,230,440,260,Choice2,Choice2); // curtain button
			settextstyle(2,0,4);
			setcolor(BLACK);

			if( Choice1 == 1 ){

				if( ROOF == CLOSE )
				{
					DriveRoof(OPEN);
					outtextxy(260,190,"[Enter] to close roof");
					ROOF = OPEN;
				}
				else
				{
					DriveRoof(CLOSE);
					outtextxy(260,190,"[Enter] to open roof");
					ROOF = CLOSE;
				}

			}
			if( Choice2 == 1 ){

				if( CURTAIN == CLOSE )
				{
					DriveCurtain(OPEN);
					outtextxy(260,240,"[Enter] to close curtain");
					CURTAIN = OPEN;
				}
				else
				{
					DriveCurtain(CLOSE);
					outtextxy(260,240,"[Enter] to open curtain");
					CURTAIN = CLOSE;
				}

			}
			button(200,180,440,210,!ACTIVE,Choice1); // roof button
			button(200,230,440,260,!ACTIVE,Choice2); // curtain button
			settextstyle(2,0,4);
			setcolor(BLACK);
			if( ROOF )
				outtextxy(260,190,"[Enter] to close roof");
			else
				outtextxy(260,190,"[Enter] to open roof");

			if( CURTAIN )
				outtextxy(260,240,"[Enter] to close curtain");
			else
				outtextxy(260,240,"[Enter] to open curtain");

		}
	}while( ch != 27 );   // Do until press ESC
	button(350,310,450,370,1,1); // exit button
	setcolor(BLACK);
	outtextxy(365,335,"[ESC] to exit");
	delay(300);
}

void StartStop_Control()
{
	int Evant;
	Before = Inport_();
	// if control is running
	windows(450,50,630,440,"Automatic control");
	settextstyle(2,0,4);
	setcolor(BLACK);
	outtextxy(480,420,"Press [ESC] for EXIT");

	do
	{
		if( ObjectBalance() )
		{
			// PAUSE WAIT EVANTHANDING
			do {
				Evant = EvantHanding();
			}while( Evant == 0 );
			// HAPPEN
			if( Evant == 1 )
			{
				if( CheckRain() == 0 )
					ROOF = 1;
				else
					ROOF = 0;
				if( CheckSunny() == 0 )
					CURTAIN = 1;
				else
					CURTAIN = 0;
				Display();
				OutportCenter();
			}
		}
		else  {
			OutportCenter();

		}
	}while( Evant != -1 );

}

void Display()
{
       textbox(40,60,430,430,BLACK);
       setlinestyle(0,0,2);
       setcolor(WHITE);
       rectangle(110,180,250,370);
       line(110,180,100,145);
       line(100,145,240,145);
       line(240,145,250,180);
       setfillstyle(1,LIGHTGRAY);
       floodfill(150,200,WHITE);
       setfillstyle(1,LIGHTGRAY);
		 floodfill(150,150,WHITE);
       settextstyle(2,0,4);
       setcolor(RED);
       outtextxy(140,200,"Genius curtain");
       setfillstyle(1,BLACK);
       bar(130,360,230,250);


       if( !CURTAIN )
       {
		setfillstyle(1,BLUE);
		bar(130,360,179,250);
		bar(181,360,230,250);
		setcolor(LIGHTBLUE);
		outtextxy(300,280,"Curtain = Close");
       }else{
		setcolor(LIGHTBLUE);
		outtextxy(300,280,"Curtain = Open");
       }

		 if( !ROOF )
       {
		setlinestyle(0,0,2);
		setcolor(DARKGRAY);
		line(250,230,260,260);
		line(260,260,120,260);
		line(120,260,110,230);
		line(110,230,250,230);
		setfillstyle(1,GREEN);
		floodfill(200,250,DARKGRAY);
		setcolor(GREEN);
		outtextxy(300,240,"Roof = Close");
       }else{
		setlinestyle(0,0,2);
		setcolor(DARKGRAY);
		line(250,230,260,200);
		line(260,200,120,200);
		line(120,200,110,230);
		line(110,230,250,230);
		setfillstyle(1,GREEN);
		floodfill(200,210,DARKGRAY);
		setcolor(GREEN);
		outtextxy(300,240,"Roof = Open");
       }

}


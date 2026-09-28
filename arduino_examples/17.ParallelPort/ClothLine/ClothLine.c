/*
  ClothLine  (ArduinoAI 2.5 หมวด 17 จาก Turbo C พอร์ตขนาน สู่ MicroPython)
  โค้ด Turbo C เดิมของครู: Project/ClothLine/ROWTAKPH.C
  ราวตากผ้าอัตโนมัติ: ฝนตกหรือไม่มีแดด เก็บราวเข้าที่ร่มและเปิดพัดลม
  โปรแกรมนี้รันบน DOS (Turbo C 2.0/3.0) คุมฮาร์ดแวร์ผ่านพอร์ตขนาน LPT1: 0x378 = ขาข้อมูล D0-D7, 0x379 = ขาสถานะ S3-S7
  ไฟล์ .py ในโฟลเดอร์เดียวกันคือโค้ดเดียวกันที่แปลงเป็น MicroPython
*/

#include<stdio.h>
#include<conio.h>
#include<string.h>
#include<graphics.h>

void Open_Graph( char *dir);
void windows(int x1, int y1, int x2, int y2, char *texttitle);
void button(int x1, int y1, int x2 ,int y2, int active, int select);
void line3d(int x1, int y1, int x2, int y2);
void textbox(int x1, int y1, int x2, int y2, int colorbg);
void groupbox(int x1, int y1, int x2, int y2, char *text);
void status_bar(int x1, int y1, int x2, int y2, char *txtstatus);
int Caltextlength( char *txt );
void label(int x1, int y1, int x2, int y2, int color, char *text);
int Main_menu( int choice );
void ShowSelect_menu( int choice );
int ExitMenu( void );
void Status_box();
void New_delay( int N );
void Manual_Control();
void Start_Control();
void Stop_Control();
void Readport();
void Control_Door(int action );
void Control_Fan( int action );

int door = 1, fan = 0;
int Weather_Sunny = 0;
int Weather_Rain = 0;
int CHKControl = 0;

int main(void)
{
	int choice = 0;
	int Done = 0;

	Open_Graph("../BGI/");
	clearviewport();

	Control_Door(1);

	do{
		choice = Main_menu(choice);
		switch( choice )
		{
			case 0 : break;
			case 1 : Start_Control(); break;
			case 2 : Stop_Control(); break;
			case 3 : Manual_Control(); break;
			case 5 : Done = ExitMenu(); break;
		}

	}while( !Done );
	return 0;
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

void label(int x1, int y1, int x2, int y2, int color, char *text)
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
	line3d(x1,y1,x1+5,y1);
	line3d(x1+11+lengthtext,y1,x2,y1);
	line3d(x1,y1,x1,y2);
	line3d(x1,y2,x2,y2);
	line3d(x2,y1,x2,y2);
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

void ShowSelect_menu( int choice )
{
	char Descript[6][300];

	strcpy(Descript[1],"  Start auto control device\n\n\
				     if select this menu then program will be  start to\
				 control device automatic. All part of device\
				 will be enable.\n\n\
					Please [Enter] to select this menu.");

	strcpy(Descript[2],"  Stop auto control device\n\n\
					  if select this menu then program will be  stop\
				 control. All part of device will be \ndisable.\n\n\
				   Please [Enter] to select this menu.");

	strcpy(Descript[3],"  Start manual control device\n\n\
				     if select this menu then program will turn\
				to mannaul mode. In this mode, device have \ncontrol\
				 by user. Such as,open fan and open\ndoor.\n\n\
				  Please [Enter] to select this menu.");

	strcpy(Descript[4],"  Program ......... by......");

	strcpy(Descript[5],"   Please [Enter] to select menu.");
	switch( choice )
	{
		case 0 : {
			label(50,75,240,110,GREEN,"  Status");
			label(50,110,240,145,WHITE,"  Start control");
			label(50,145,240,180,WHITE,"  Stop control");
			label(50,180,240,215,WHITE,"  Manual control");
			label(50,215,240,250,WHITE,"  About us");
			label(50,250,240,285,WHITE,"  Exit");

		}break;
		case 1 : {
			label(50,75,240,110,WHITE,"  Status");
			label(50,110,240,145,GREEN,"  Start control");
			label(50,145,240,180,WHITE,"  Stop control");
			label(50,180,240,215,WHITE,"  Manual control");
			label(50,215,240,250,WHITE,"  About us");
			label(50,250,240,285,WHITE,"  Exit");
		}break;
		case 2 : {
			label(50,75,240,110,WHITE,"  Status");
			label(50,110,240,145,WHITE,"  Start control");
			label(50,145,240,180,GREEN,"  Stop control");
			label(50,180,240,215,WHITE,"  Manual control");
			label(50,215,240,250,WHITE,"  About us");
			label(50,250,240,285,WHITE,"  Exit");
		}break;
		case 3 : {
			label(50,75,240,110,WHITE,"  Status");
			label(50,110,240,145,WHITE,"  Start control");
			label(50,145,240,180,WHITE,"  Stop control");
			label(50,180,240,215,GREEN,"  Manual control");
			label(50,215,240,250,WHITE,"  About us");
			label(50,250,240,285,WHITE,"  Exit");
		}break;
		case 4 : {
			label(50,75,240,110,WHITE,"  Status");
			label(50,110,240,145,WHITE,"  Start control");
			label(50,145,240,180,WHITE,"  Stop control");
			label(50,180,240,215,WHITE,"  Manual control");
			label(50,215,240,250,GREEN,"  About us");
			label(50,250,240,285,WHITE,"  Exit");
		}break;
		case 5 : {
			label(50,75,240,110,WHITE,"  Status");
			label(50,110,240,145,WHITE,"  Start control");
			label(50,145,240,180,WHITE,"  Stop control");
			label(50,180,240,215,WHITE,"  Manual control");
			label(50,215,240,250,WHITE,"  About us");
			label(50,250,240,285,GREEN,"  Exit");
		}break;
	}
	if( choice != 0 )
		label(300,65,605,240,LIGHTGRAY,Descript[choice]);
	else{
		label(300,65,605,240,LIGHTGRAY,"");
		settextstyle(2,0,4);
		setcolor(BLACK);
		outtextxy(315,80,"Welcome to my program.");
		outtextxy(315,120,"Weather today,");
		if( Weather_Sunny ) outtextxy(330,140,"Sunny    : YES");
		else outtextxy(330,140,"Sunny    : NO");
		if( Weather_Rain ) outtextxy(330,160,"Raining   : YES");
		else outtextxy(330,160,"Raining   : NO");
	}

}
void Readport()
{
	int value;
	value = inportb(0x379);

	if( (value&128) == 128 )
		Weather_Rain = 0;
	else
		Weather_Rain = 1;

	if( (value&32) == 32 )
		Weather_Sunny = 0;
	else
		Weather_Sunny = 1;

	if( Weather_Rain == 1 )
	{
		if( door == 1 ) CHKControl = 1;
		door = 0;
		fan = 1;
	}
	else if( Weather_Sunny == 0 )
	{
		if( door == 1 ) CHKControl = 1;
		door = 0;
		fan = 1;
	}
	else
	{
		if( door == 0 ) CHKControl = 1;
		door = 1;
		fan = 0;
	}

}

void Status_box()
{
	static int i = 0;

	if( i == 0 ) i = 1;
	else i = 0;
	groupbox(290,280,610,430,"Display");
	textbox(300,290,600,420,BLACK);


	setlinestyle(0,0,1);
	setcolor(WHITE);
	rectangle(350,300,430,380);
	line(390,303,390,377);
	setfillstyle(1,BLUE);
	settextstyle(2,0,4);
	if( door )
	{
		bar(352,301,369,379);
		bar(411,301,428,379);
		setcolor(WHITE);
		outtextxy(350,390," Door : Open");
	}else{
		bar(352,301,389,379);
		bar(391,301,428,379);
		setcolor(WHITE);
		outtextxy(350,390," Door : Close");
	}

	setlinestyle(0,0,1);
	setcolor(WHITE);
	circle(500,340,45);
	setfillstyle(1,BLACK);
	floodfill(500,340,WHITE);

	settextstyle(2,0,4);
	setcolor(WHITE);
	if( fan )
	{
		outtextxy(470,390,"Fan : Open");
		if( i == 1 )
		{
			setcolor(GREEN);
			pieslice(500,340,90,135,40);
			pieslice(500,340,270,315,40);
			pieslice(500,340,180,225,40);
			pieslice(500,340,0,45,40);
			setfillstyle(1,GREEN);
			floodfill(490,310,GREEN);
			floodfill(520,330,GREEN);
			floodfill(480,350,GREEN);
			floodfill(520,370,GREEN);
		}else{
			setcolor(GREEN);
			pieslice(500,340,135,180,40);
			pieslice(500,340,315,360,40);
			pieslice(500,340,225,270,40);
			pieslice(500,340,45,90,40);
			setfillstyle(1,GREEN);
			floodfill(520,310,GREEN);
			floodfill(480,330,GREEN);
			floodfill(520,350,GREEN);
			floodfill(480,370,GREEN);
		}

	}else{
		outtextxy(470,390,"Fan : Close");
		setcolor(GREEN);
		pieslice(500,340,90,135,40);
		pieslice(500,340,270,315,40);
		pieslice(500,340,180,225,40);
		pieslice(500,340,0,45,40);
		setfillstyle(1,GREEN);
		floodfill(490,310,GREEN);
		floodfill(520,330,GREEN);
		floodfill(480,350,GREEN);
		floodfill(520,370,GREEN);
	}
}

int Main_menu( int Old_Choice )
{
	char ch = 0;
	int Choice;
	Choice = Old_Choice;
	windows(1,1,639,479,"Control");
	status_bar(2,460,638,478,"[^] [v] to select menu ");
	groupbox(30,50,260,430,"Menu");
	textbox(40,60,250,420,WHITE);
	groupbox(290,50,610,250,"Descript");
	ShowSelect_menu( Old_Choice );

	do{
		do{
			ch = 0;
			Readport();
			Status_box();
			if( Choice == 0 ) ShowSelect_menu( Choice );
			New_delay(500);
			if( CHKControl == 1 )
			{
				Control_Door( door );
				Control_Fan( fan );
				CHKControl = 0;
			}
			if( kbhit() ) ch = getch();

		}while( ch != 72 && ch != 80 && ch != 13);
		if( ch != 13 )
		{
			switch(ch)
			{
				case 72 : Choice--; break;
				case 80 : Choice++; break;
			}
			if( Choice == -1 ) Choice = 5;
			if( Choice == 6 ) Choice = 0;
		}
		ShowSelect_menu( Choice );
	}while( ch != 13 );
	return Choice;
}

int ExitMenu( void )
{
	char ch = 0;
	int choice1 = 0,choice2 = 1;
	windows(210,160,430,280,"Exit");
	label(230,190,420,250,LIGHTGRAY,"Do you want to exit program?");
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
		outport(0x378,0);
		return 1;
	}
}

void New_delay( int N )
{
	int i = 0;
	do{
		delay(1);
		i++;
	}while( i < N && !kbhit() );

}

void Manual_Control()
{
	int Choice1 = 1, Choice2 = 0;
	char ch = 0;

	CHKControl = 0;
	windows(150,100,490,380,"Manual control");
	groupbox(170,140,470,300,"Control");
	button(200,180,440,210,0,Choice1);
	button(200,230,440,260,0,Choice2);
	button(350,310,450,370,0,0);
	settextstyle(2,0,4);
	setcolor(BLACK);
	outtextxy(180,320,"[^] [v] to select menu");
	outtextxy(365,335,"[ESC] to exit");
	if( door )
		outtextxy(260,190,"[Enter] to close door");
	else
		outtextxy(260,190,"[Enter] to open door");

	if( fan )
		outtextxy(260,240,"[Enter] to close fan");
	else
		outtextxy(260,240,"[Enter] to open fan");

	do{
		do{
			ch = getch();
		}while( ch != 72 && ch != 80 && ch != 27 && ch != 13 );

		if( ch == 72 || ch == 80 )
		{
			if( Choice1 == 1 )
			{
				Choice1 = 0;
				Choice2 = 1;

			}else{
				Choice1 = 1;
				Choice2 = 0;
			}
			button(200,180,440,210,0,Choice1);
			button(200,230,440,260,0,Choice2);
			settextstyle(2,0,4);
			setcolor(BLACK);
			if( door )
				outtextxy(260,190,"[Enter] to close door");
			else
				outtextxy(260,190,"[Enter] to open door");

			if( fan )
				outtextxy(260,240,"[Enter] to close fan");
			else
				outtextxy(260,240,"[Enter] to open fan");

		}
		if( ch == 13 )
		{
			button(200,180,440,210,Choice1,Choice1);
			button(200,230,440,260,Choice2,Choice2);
			settextstyle(2,0,4);
			setcolor(BLACK);
			if( door )
				outtextxy(260,190,"[Enter] to close door");
			else
				outtextxy(260,190,"[Enter] to open door");

			if( fan )
				outtextxy(260,240,"[Enter] to close fan");
			else
				outtextxy(260,240,"[Enter] to open fan");

			delay(300);

			if( Choice1 == 1 ){
				if( door ) door = 0;
				else door = 1;

			}
			else{
				if( fan ) fan = 0;
				else fan = 1;
			}
			button(200,180,440,210,0,Choice1);
			button(200,230,440,260,0,Choice2);
			settextstyle(2,0,4);
			setcolor(BLACK);
			if( door )
				outtextxy(260,190,"[Enter] to close door");
			else
				outtextxy(260,190,"[Enter] to open door");

			if( fan )
				outtextxy(260,240,"[Enter] to close fan");
			else
				outtextxy(260,240,"[Enter] to open fan");

			Control_Door(door);
			Control_Fan(fan);

		}
	}while( ch != 27 );
	button(350,310,450,370,1,1);
	setcolor(BLACK);
	outtextxy(365,335,"[ESC] to exit");
	delay(300);
}
void Start_Control()
{
	windows(170,180,470,300,"Start control by automatic");
	settextstyle(2,0,4);
	setcolor(BLACK);

	if( CHKControl )
		outtextxy(220,240,"Now, Automatic control is running..");
	else
		outtextxy(200,240,"Initial hardware to control. Please wait...");
	CHKControl = 1;
	Readport();
	delay(1500);
}

void Stop_Control()
{
	outport(0x378,0);
	windows(160,180,480,300,"Stop all control");
	settextstyle(2,0,4);
	setcolor(BLACK);

	if( CHKControl || door || fan)
		outtextxy(170,240,"Program will be terminate all control. please wait...");
	else
		outtextxy(250,240,"Not control in this time.");
	CHKControl = 0;
	door = 0;
	fan = 0;
	Control_Fan(0);
	Control_Door(0);
	delay(1500);
}

void Control_Door( int action )
{
	int j = 0,a;
	int Step[4] = { 5,6,10,9 };
	if( action ){
		do{
			for(a=0;a<=150;a++)
			{
				outport(0x378,Step[j]);
				New_delay(3);
				if( j > 3 )  j = 0;
				else j++;
			}
		}while( (inportb(0x379) != 143 ));

	}else{
		do{
			for(a=0;a<=150;a++)
			{
				outport(0x378,Step[j]);
				New_delay(3);
				if( j < 0 )  j = 3;
				else j--;
			}
		}while( (inportb(0x379) != 143 ));
	}
}

void Control_Fan( int action )
{
	if( action )
	{
		outport(0x378,64);
	}
	else
	{
		outport(0x378,0);
	}
}


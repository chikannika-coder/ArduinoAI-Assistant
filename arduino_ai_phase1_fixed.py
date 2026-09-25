# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re


# ============================================================
# Arduino AI Code Generator
# ============================================================

class ArduinoCodeGenerator:

    def generate(self, command):
        command = command.lower().strip()

        if not command:
            return "// กรุณาใส่คำสั่ง"

        # -----------------------------------------
        # SERVO
        # -----------------------------------------
        if "servo" in command or "เซอร์โว" in command:
            return self.generate_servo(command)

        # -----------------------------------------
        # ULTRASONIC
        # -----------------------------------------
        if (
            "ultrasonic" in command
            or "อัลตราโซนิก" in command
            or "ระยะทาง" in command
        ):
            return self.generate_ultrasonic(command)

        # -----------------------------------------
        # BUZZER
        # -----------------------------------------
        if "buzzer" in command or "เสียง" in command or "บัซเซอร์" in command:
            return self.generate_buzzer(command)

        # -----------------------------------------
        # LED
        # -----------------------------------------
        if "led" in command or "ไฟ" in command:
            return self.generate_led(command)

        return """
// ========================================
// Arduino AI Assistant
// ========================================
//
// ยังไม่เข้าใจคำสั่ง:
//
// รองรับคำสั่งเบื้องต้น:
// - LED
// - Servo
// - Buzzer
// - Ultrasonic
//
// ตัวอย่าง:
// ให้ LED ขา 13 กระพริบทุก 1 วินาที
// ให้ Servo ขา 9 หมุนไป 90 องศา
// ให้ Buzzer ขา 8 ส่งเสียง
// อ่านระยะทาง Ultrasonic trig 9 echo 10
//
"""

    # ========================================================
    # LED
    # ========================================================

    def generate_led(self, command):

        pin = self.extract_pin(command, default=13)
        delay_time = self.extract_time(command, default=1000)

        # เปิด LED
        if "เปิด" in command and "กระพริบ" not in command:
            return f"""
#define LED_PIN {pin}

void setup() {{

    pinMode(LED_PIN, OUTPUT);

    digitalWrite(LED_PIN, HIGH);

}}

void loop() {{

}}
"""

        # ปิด LED
        if "ปิด" in command.replace("เปิด", "") and "กระพริบ" not in command:
            return f"""
#define LED_PIN {pin}

void setup() {{

    pinMode(LED_PIN, OUTPUT);

    digitalWrite(LED_PIN, LOW);

}}

void loop() {{

}}
"""

        # LED Blink
        return f"""
#define LED_PIN {pin}

void setup() {{

    pinMode(LED_PIN, OUTPUT);

}}

void loop() {{

    digitalWrite(LED_PIN, HIGH);

    delay({delay_time});

    digitalWrite(LED_PIN, LOW);

    delay({delay_time});

}}
"""

    # ========================================================
    # SERVO
    # ========================================================

    def generate_servo(self, command):

        pin = self.extract_pin(command, default=9)

        angle = self.extract_angle(command, default=90)

        return f"""
#include <Servo.h>

Servo myServo;

void setup() {{

    myServo.attach({pin});

    myServo.write({angle});

}}

void loop() {{

}}
"""

    # ========================================================
    # BUZZER
    # ========================================================

    def generate_buzzer(self, command):

        pin = self.extract_pin(command, default=8)

        frequency = 1000

        return f"""
#define BUZZER_PIN {pin}

void setup() {{

    pinMode(BUZZER_PIN, OUTPUT);

}}

void loop() {{

    tone(BUZZER_PIN, {frequency});

    delay(1000);

    noTone(BUZZER_PIN);

    delay(1000);

}}
"""

    # ========================================================
    # ULTRASONIC
    # ========================================================

    def generate_ultrasonic(self, command):

        numbers = re.findall(r"\d+", command)

        trig = 9
        echo = 10

        if len(numbers) >= 2:
            trig = numbers[0]
            echo = numbers[1]

        return f"""
#define TRIG_PIN {trig}
#define ECHO_PIN {echo}

long duration;
float distance;

void setup() {{

    Serial.begin(9600);

    pinMode(TRIG_PIN, OUTPUT);

    pinMode(ECHO_PIN, INPUT);

}}

void loop() {{

    digitalWrite(TRIG_PIN, LOW);

    delayMicroseconds(2);

    digitalWrite(TRIG_PIN, HIGH);

    delayMicroseconds(10);

    digitalWrite(TRIG_PIN, LOW);


    duration = pulseIn(ECHO_PIN, HIGH);


    distance = duration * 0.0343 / 2;


    Serial.print("Distance: ");

    Serial.print(distance);

    Serial.println(" cm");


    delay(500);

}}
"""

    # ========================================================
    # Extract PIN
    # ========================================================

    def extract_pin(self, command, default=13):

        patterns = [

            r"ขา\s*(\d+)",

            r"pin\s*(\d+)",

            r"gpio\s*(\d+)"

        ]

        for pattern in patterns:

            result = re.search(pattern, command)

            if result:

                return int(result.group(1))

        return default

    # ========================================================
    # Extract angle
    # ========================================================

    def extract_angle(self, command, default=90):

        result = re.search(
            r"(\d+)\s*(องศา|degree|degrees)",
            command
        )

        if result:

            angle = int(result.group(1))

            angle = max(0, min(angle, 180))

            return angle

        return default

    # ========================================================
    # Extract time
    # ========================================================

    def extract_time(self, command, default=1000):

        # seconds
        result = re.search(
            r"(\d+(?:\.\d+)?)\s*วินาที",
            command
        )

        if result:

            seconds = float(result.group(1))

            return int(seconds * 1000)

        # milliseconds
        result = re.search(
            r"(\d+)\s*(ms|มิลลิวินาที)",
            command
        )

        if result:

            return int(result.group(1))

        return default


# ============================================================
# GUI
# ============================================================

class ArduinoAIGUI:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Arduino AI Assistant - Phase 1"
        )

        self.root.geometry(
            "1100x750"
        )

        self.generator = ArduinoCodeGenerator()

        self.create_widgets()

    # ========================================================
    # UI
    # ========================================================

    def create_widgets(self):

        # Header
        header = ttk.Label(
            self.root,
            text="Arduino AI Assistant",
            font=("Arial", 24, "bold")
        )

        header.pack(
            pady=15
        )

        subtitle = ttk.Label(
            self.root,
            text="Thai Language → Arduino Code",
            font=("Arial", 12)
        )

        subtitle.pack(
            pady=5
        )

        # ------------------------------------------
        # Command frame
        # ------------------------------------------

        command_frame = ttk.LabelFrame(
            self.root,
            text="คำสั่งภาษาไทย"
        )

        command_frame.pack(
            fill="x",
            padx=20,
            pady=10
        )

        self.command_entry = tk.Text(
            command_frame,
            height=4,
            font=("Arial", 14)
        )

        self.command_entry.pack(
            fill="x",
            padx=10,
            pady=10
        )

        # default command
        self.command_entry.insert(
            "1.0",
            "ให้ LED ขา 13 กระพริบทุก 1 วินาที"
        )

        # ------------------------------------------
        # Generate Button
        # ------------------------------------------

        generate_button = ttk.Button(
            command_frame,
            text="Generate Arduino Code",
            command=self.generate_code
        )

        generate_button.pack(
            pady=10
        )

        # ------------------------------------------
        # Code frame
        # ------------------------------------------

        code_frame = ttk.LabelFrame(
            self.root,
            text="Arduino Code"
        )

        code_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        self.code_text = tk.Text(
            code_frame,
            font=("Consolas", 12),
            wrap="none"
        )

        self.code_text.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        # ------------------------------------------
        # Bottom buttons
        # ------------------------------------------

        button_frame = ttk.Frame(
            self.root
        )

        button_frame.pack(
            pady=10
        )

        ttk.Button(
            button_frame,
            text="Copy Code",
            command=self.copy_code
        ).grid(
            row=0,
            column=0,
            padx=5
        )

        ttk.Button(
            button_frame,
            text="Save .ino",
            command=self.save_code
        ).grid(
            row=0,
            column=1,
            padx=5
        )

        ttk.Button(
            button_frame,
            text="Clear",
            command=self.clear
        ).grid(
            row=0,
            column=2,
            padx=5
        )

    # ========================================================
    # Generate
    # ========================================================

    def generate_code(self):

        command = self.command_entry.get(
            "1.0",
            tk.END
        ).strip()

        code = self.generator.generate(
            command
        )

        self.code_text.delete(
            "1.0",
            tk.END
        )

        self.code_text.insert(
            "1.0",
            code
        )

    # ========================================================
    # Copy
    # ========================================================

    def copy_code(self):

        code = self.code_text.get(
            "1.0",
            tk.END
        )

        self.root.clipboard_clear()

        self.root.clipboard_append(
            code
        )

        messagebox.showinfo(
            "Arduino AI",
            "Copy Code เรียบร้อย"
        )

    # ========================================================
    # Save
    # ========================================================

    def save_code(self):

        code = self.code_text.get(
            "1.0",
            tk.END
        )

        filename = filedialog.asksaveasfilename(

            defaultextension=".ino",

            filetypes=[
                (
                    "Arduino Sketch",
                    "*.ino"
                )
            ]

        )

        if filename:

            with open(
                filename,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(
                    code
                )

            messagebox.showinfo(
                "Arduino AI",
                "บันทึก Arduino Code เรียบร้อย"
            )

    # ========================================================
    # Clear
    # ========================================================

    def clear(self):

        self.command_entry.delete(
            "1.0",
            tk.END
        )

        self.code_text.delete(
            "1.0",
            tk.END
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = ArduinoAIGUI(
        root
    )

    root.mainloop()

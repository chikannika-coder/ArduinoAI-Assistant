// ARDUINO CODE FOR PYTHON AI HAND TRACKING CONTROL
#include <Servo.h>

// Create servo objects
Servo thumbServo;
Servo indexServo;
Servo middleServo;
Servo ringServo;
Servo pinkyServo;

// Pin configuration - YOUR CORRECT PINS
const int THUMB_PIN = 10;   // Thumb
const int INDEX_PIN = 9;    // Index finger
const int MIDDLE_PIN = 6;   // Middle finger
const int RING_PIN = 5;     // Ring finger
const int PINKY_PIN = 3;    // Pinky finger

// Angle limits
const int MIN_ANGLE = 0;    // Fully open (fingers up)
const int MAX_ANGLE = 90;   // Fully closed (fingers down)

// For storing current angles
int currentAngles[5] = {0, 0, 0, 0, 0};
String fingerNames[5] = {"Thumb", "Index", "Middle", "Ring", "Pinky"};

void setup() {
  Serial.begin(9600);
  Serial.println("AI HAND CONTROLLER - READY");
  Serial.println("Waiting for Python commands...");
  
  // Attach servos to pins
  thumbServo.attach(THUMB_PIN);
  indexServo.attach(INDEX_PIN);
  middleServo.attach(MIDDLE_PIN);
  ringServo.attach(RING_PIN);
  pinkyServo.attach(PINKY_PIN);
  
  // Start with fingers open
  openAllFingers();
  delay(1000);
}

void loop() {
  // Listen for commands from Python
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.length() > 0) {
      processCommand(command);
    }
  }
}

void processCommand(String cmd) {
  // Debug: print received command
  // Serial.print("Got: ");
  // Serial.println(cmd);
  
  // COMMAND TYPE 1: Individual finger - "T:45" (Thumb to 45 degrees)
  if (cmd.length() >= 3 && cmd.indexOf(':') == 1) {
    char fingerCode = cmd.charAt(0);  // First character: T, I, M, R, P
    String angleStr = cmd.substring(2);  // After ":"
    int angle = angleStr.toInt();
    
    // Make sure angle is within limits
    angle = constrain(angle, MIN_ANGLE, MAX_ANGLE);
    
    // Move the appropriate finger
    switch(fingerCode) {
      case 'T':  // Thumb
        thumbServo.write(angle);
        currentAngles[0] = angle;
        break;
      case 'I':  // Index
        indexServo.write(angle);
        currentAngles[1] = angle;
        break;
      case 'M':  // Middle
        middleServo.write(angle);
        currentAngles[2] = angle;
        break;
      case 'R':  // Ring
        ringServo.write(angle);
        currentAngles[3] = angle;
        break;
      case 'P':  // Pinky
        pinkyServo.write(angle);
        currentAngles[4] = angle;
        break;
    }
    
    // Optional: send confirmation back to Python
    // Serial.print("OK:");
    // Serial.println(cmd);
  }
  
  // COMMAND TYPE 2: All fingers at once - "ALL:T45,I30,M60,R20,P90"
  else if (cmd.startsWith("ALL:")) {
    String allData = cmd.substring(4);  // Remove "ALL:"
    
    // Split by commas
    int startIndex = 0;
    for (int i = 0; i < 5; i++) {
      int commaIndex = allData.indexOf(',', startIndex);
      String fingerCmd;
      
      if (commaIndex == -1 && i == 4) {
        // Last finger, no comma
        fingerCmd = allData.substring(startIndex);
      } else {
        fingerCmd = allData.substring(startIndex, commaIndex);
        startIndex = commaIndex + 1;
      }
      
      if (fingerCmd.length() >= 2) {
        char fingerCode = fingerCmd.charAt(0);
        String angleStr = fingerCmd.substring(1);
        int angle = angleStr.toInt();
        angle = constrain(angle, MIN_ANGLE, MAX_ANGLE);
        
        // Move finger
        switch(fingerCode) {
          case 'T':
            thumbServo.write(angle);
            currentAngles[0] = angle;
            break;
          case 'I':
            indexServo.write(angle);
            currentAngles[1] = angle;
            break;
          case 'M':
            middleServo.write(angle);
            currentAngles[2] = angle;
            break;
          case 'R':
            ringServo.write(angle);
            currentAngles[3] = angle;
            break;
          case 'P':
            pinkyServo.write(angle);
            currentAngles[4] = angle;
            break;
        }
      }
    }
    
    // Optional: send confirmation
    // Serial.println("OK:ALL");
  }
  
  // COMMAND TYPE 3: Sequence commands
  else if (cmd.startsWith("SEQ:")) {
    String seqName = cmd.substring(4);
    
    if (seqName == "wave") {
      waveSequence();
    } else if (seqName == "fist") {
      fistSequence();
    } else if (seqName == "open") {
      openAllFingers();
    } else if (seqName == "test") {
      testSequence();
    }
    
    // Serial.print("OK:SEQ:");
    // Serial.println(seqName);
  }
  
  // COMMAND TYPE 4: Reset/Open all
  else if (cmd == "OPEN") {
    openAllFingers();
    // Serial.println("OK:OPEN");
  }
  
  // COMMAND TYPE 5: Close all
  else if (cmd == "CLOSE") {
    closeAllFingers();
    // Serial.println("OK:CLOSE");
  }
  
  // COMMAND TYPE 6: Test command
  else if (cmd == "TEST") {
    testSequence();
    // Serial.println("OK:TEST");
  }
}

// ========== MOVEMENT FUNCTIONS ==========

void openAllFingers() {
  thumbServo.write(MIN_ANGLE);
  indexServo.write(MIN_ANGLE);
  middleServo.write(MIN_ANGLE);
  ringServo.write(MIN_ANGLE);
  pinkyServo.write(MIN_ANGLE);
  
  for (int i = 0; i < 5; i++) {
    currentAngles[i] = MIN_ANGLE;
  }
}

void closeAllFingers() {
  thumbServo.write(MAX_ANGLE);
  indexServo.write(MAX_ANGLE);
  middleServo.write(MAX_ANGLE);
  ringServo.write(MAX_ANGLE);
  pinkyServo.write(MAX_ANGLE);
  
  for (int i = 0; i < 5; i++) {
    currentAngles[i] = MAX_ANGLE;
  }
}

void waveSequence() {
  // Pinky
  pinkyServo.write(MAX_ANGLE);
  delay(200);
  pinkyServo.write(MIN_ANGLE);
  delay(200);
  
  // Ring
  ringServo.write(MAX_ANGLE);
  delay(200);
  ringServo.write(MIN_ANGLE);
  delay(200);
  
  // Middle
  middleServo.write(MAX_ANGLE);
  delay(200);
  middleServo.write(MIN_ANGLE);
  delay(200);
  
  // Index
  indexServo.write(MAX_ANGLE);
  delay(200);
  indexServo.write(MIN_ANGLE);
  delay(200);
  
  // Thumb
  thumbServo.write(MAX_ANGLE);
  delay(200);
  thumbServo.write(MIN_ANGLE);
}

void fistSequence() {
  // Close all fingers
  closeAllFingers();
  delay(1000);
  
  // Open all fingers
  openAllFingers();
  delay(1000);
}

void testSequence() {
  Serial.println("=== TESTING ALL FINGERS ===");
  
  Serial.println("1. Thumb...");
  thumbServo.write(MAX_ANGLE);
  delay(500);
  thumbServo.write(MIN_ANGLE);
  delay(500);
  
  Serial.println("2. Index...");
  indexServo.write(MAX_ANGLE);
  delay(500);
  indexServo.write(MIN_ANGLE);
  delay(500);
  
  Serial.println("3. Middle...");
  middleServo.write(MAX_ANGLE);
  delay(500);
  middleServo.write(MIN_ANGLE);
  delay(500);
  
  Serial.println("4. Ring...");
  ringServo.write(MAX_ANGLE);
  delay(500);
  ringServo.write(MIN_ANGLE);
  delay(500);
  
  Serial.println("5. Pinky...");
  pinkyServo.write(MAX_ANGLE);
  delay(500);
  pinkyServo.write(MIN_ANGLE);
  
  Serial.println("=== TEST COMPLETE ===");
}

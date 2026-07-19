#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// Pin Definitions based on the schematic layout
#define BTN_START      12   // Start Button
#define BTN_MODE       14   // Mode Selection Button
#define VIB_MOTOR      25   // Vibration Motor driver pin
#define I2C_SDA        21   // ESP32 Hardware SDA
#define I2C_SCL        22   // ESP32 Hardware SCL

// Initialize 20x4 LCD at I2C address 0x27 (common for PCF8574)
LiquidCrystal_I2C lcd(0x27, 20, 4);

// Global Variables for Sensor Metrics
int heartRate = 72;
int spo2 = 98;
float bodyTemp = 36.5;
float ecgValue = 1.2;
String motionStatus = "STABLE";

unsigned long lastUpdate = 0;
const long interval = 1000; // Update display every 1 second

void setup() {
  // Initialize Serial for receiving simulated sensor data from the Pi
  Serial.begin(115200);
  
  // Initialize I2C with explicit pins
  Wire.begin(I2C_SDA, I2C_SCL);
  
  // Initialize LCD
  lcd.init();
  lcd.backlight();
  
  // Initialize GPIOs
  pinMode(BTN_START, INPUT_PULLUP);
  pinMode(BTN_MODE, INPUT_PULLUP);
  pinMode(VIB_MOTOR, OUTPUT);
  
  // Boot Screen
  lcd.setCursor(2, 0);
  lcd.print("WEARABLE 5-VITALS");
  lcd.setCursor(4, 1);
  lcd.print("MONITOR SYSTEM");
  lcd.setCursor(3, 3);
  lcd.print("Initializing...");
  delay(2000);
  lcd.clear();
}

void loop() {
  // 1. Check for Simulated Sensor Input via Serial Stream
  if (Serial.available() > 0) {
    String incomingData = Serial.readStringUntil('\n');
    parseSimulatedData(incomingData);
  }

  // 2. Button Logic Actions
  if (digitalRead(BTN_START) == LOW) {
    // Trigger motor haptic response on press
    digitalWrite(VIB_MOTOR, HIGH);
    delay(200);
    digitalWrite(VIB_MOTOR, LOW);
  }

  // 3. Update the 20x4 Screen Display periodically
  if (millis() - lastUpdate >= interval) {
    lastUpdate = millis();
    updateDisplay();
  }
}

// Expects format: HR,SPO2,TEMP,ECG,MOTION (e.g., "75,99,36.8,1.4,MOVING")
void parseSimulatedData(String data) {
  data.trim();
  if (data.length() == 0) return;

  int comma1 = data.indexOf(',');
  int comma2 = data.indexOf(',', comma1 + 1);
  int comma3 = data.indexOf(',', comma2 + 1);
  int comma4 = data.indexOf(',', comma3 + 1);

  if (comma1 != -1 && comma2 != -1 && comma3 != -1 && comma4 != -1) {
    heartRate = data.substring(0, comma1).toInt();
    spo2 = data.substring(comma1 + 1, comma2).toInt();
    bodyTemp = data.substring(comma2 + 1, comma3).toFloat();
    ecgValue = data.substring(comma3 + 1, comma4).toFloat();
    motionStatus = data.substring(comma4 + 1);
  }
}

void updateDisplay() {
  // Line 0: Title or System Status
  lcd.setCursor(0, 0);
  lcd.print("--- VITAL SIGNS --- ");

  // Line 1: Heart Rate & SpO2
  lcd.setCursor(0, 1);
  lcd.print("HR: ");
  lcd.print(heartRate);
  lcd.print("bpm   ");
  lcd.setCursor(11, 1);
  lcd.print("SpO2: ");
  lcd.print(spo2);
  lcd.print("%");

  // Line 2: Temperature & ECG Signal
  lcd.setCursor(0, 2);
  lcd.print("Temp: ");
  lcd.print(bodyTemp, 1);
  lcd.print("C  ");
  lcd.setCursor(12, 2);
  lcd.print("ECG: ");
  lcd.print(ecgValue, 1);
  lcd.print("V");

  // Line 3: Activity Tracking
  lcd.setCursor(0, 3);
  lcd.print("Motion: ");
  lcd.print(motionStatus);
  // Clear any trailing characters
  for (int i = motionStatus.length(); i < 12; i++) {
    lcd.print(" ");
  }
}

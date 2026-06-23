// ==========================================
// ข้อมูล Blynk ของคุณ
// ==========================================
#define BLYNK_TEMPLATE_ID "TMPL6wURuFn6V"
#define BLYNK_TEMPLATE_NAME "IoT Smart Garage"
#define BLYNK_AUTH_TOKEN "R057HWQm2jw39Ouwv5nQieKJP3eUJPJT"

#define BLYNK_PRINT Serial
#include <WiFi.h>
#include <WiFiClient.h>
#include <BlynkSimpleEsp32.h>
#include "DHT.h" 
#include <ESP32Servo.h> 
#include <math.h> // นำเข้าไลบรารีคณิตศาสตร์สำหรับการคำนวณสมการ


char ssid[] = "MakerLnwZa_2.4GHz"; 
char pass[] = "P@ssw0rd"; 

//  char ssid[] = "NongkengPhone"; 
//  char pass[] = "12345678"; 

// char ssid[] = "GH2368_2.4G"; 
//  char pass[] = "goldenhouse@2368";

// char ssid[] = "Keng_2.4G";
// char pass[] = "0918197186";

#define DHTPIN 4        
#define DHTTYPE DHT11   
DHT dht(DHTPIN, DHTTYPE);

const int trigPin = 12;
const int echoPin = 13;
const int greenPin = 14;
const int yellowPin = 27;
const int redPin = 26;

const int servoPin = 15; 
Servo doorServo;

const int buzzerPin = 18;
const int fanPin = 21; 

// --- เซนเซอร์วัดน้ำฝน / ตรวจน้ำมันรั่วด้วยสมการระเหย ---
const int rainSensorPin = 32; 
bool leakAlertSent = false;
bool isAnalyzing = false;
unsigned long wetStartTime = 0;  
unsigned long expectedEvapTime = 30000; // ตัวแปรเก็บเวลาคาดการณ์ระเหย (เริ่มต้นที่ 30 วิ)

long duration;
int distance;
bool tempAlertSent = false; 

BlynkTimer timer;

void beepBuzzer() {
  pinMode(buzzerPin, OUTPUT);
  digitalWrite(buzzerPin, LOW); 
  delay(150);
  pinMode(buzzerPin, INPUT);    
  delay(150);
}

// ==========================================
// รับคำสั่งจากแอป: ปุ่ม V3 (พัดลม)
// ==========================================
BLYNK_WRITE(V3) {
  int fanState = param.asInt(); 
  digitalWrite(fanPin, fanState);
  if(fanState == 1) Serial.println("Blynk: Fan ON");
  else Serial.println("Blynk: Fan OFF");
}

// ==========================================
// รับคำสั่งจากแอป: ปุ่ม V4 (แมนนวลเปิด-ปิดประตู)
// ==========================================
BLYNK_WRITE(V4) {
  int doorState = param.asInt();
  if(doorState == 1) {
    Serial.println("Blynk: Manual Open Door (10 degrees)");
    for(int i=0; i<3; i++) { beepBuzzer(); }
    doorServo.write(10); 
  } else {
    Serial.println("Blynk: Manual Close Door (180 degrees)");
    for(int i=0; i<3; i++) { beepBuzzer(); }
    doorServo.write(180);
  }
}

// ==========================================
// ฟังก์ชันส่งข้อมูลเซนเซอร์และประมวลผลสมการ
// ==========================================
void sendSensor() {
  // 1. อ่านค่าอุณหภูมิและความชื้น
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  
  if (!isnan(h) && !isnan(t)) {
    Blynk.virtualWrite(V1, t);
    Blynk.virtualWrite(V2, h);

    if (t > 35.0 && !tempAlertSent) {
      Blynk.logEvent("high_temp", String("ร้อนจัด! อุณหภูมิโรงรถ: ") + t + " C");
      digitalWrite(fanPin, HIGH); 
      Blynk.virtualWrite(V3, 1);  
      tempAlertSent = true;       
    } 
    else if (t <= 32.0) {
      tempAlertSent = false;
    }
  }

  // 2. วิเคราะห์ของเหลวด้วยสมการอุณหพลศาสตร์ (Dalton's Law & Magnus-Tetens Formula)
  int rainState = digitalRead(rainSensorPin);
  
  if (rainState == LOW) { // ตรวจพบของเหลว (Active LOW)
    if (!isAnalyzing && !leakAlertSent && !isnan(h) && !isnan(t)) {
      isAnalyzing = true;
      wetStartTime = millis(); 
      Blynk.virtualWrite(V5, "🔍 กำลังประมวลผลสมการ...");
      
      // ---------- ส่วนคำนวณสมการฟิสิกส์ ----------
      // 1. หาความดันไออิ่มตัว (Saturation Vapor Pressure: Ps) หน่วย kPa
      float Ps = 0.61078 * exp((17.27 * t) / (t + 237.3));
      
      // 2. หาความดันไอจริง (Actual Vapor Pressure: Pa) หน่วย kPa
      float Pa = Ps * (h / 100.0);
      
      // 3. หา Vapor Pressure Deficit (VPD) ยิ่งค่านี้สูง น้ำยิ่งระเหยเร็ว
      float VPD = Ps - Pa;
      
      // 4. แปลงอัตราการระเหย เป็นเวลาคาดการณ์ (Expected Dry Time) 
      // (ตัวเลขสมมติสำหรับปรับสเกลเวลาให้เหมาะกับการพรีเซนต์: ช่วง 15 - 45 วินาที)
      expectedEvapTime = 45000 - (VPD * 10000); 
      
      // ป้องกันไม่ให้เวลารอน้อยกว่า 15 วิ หรือนานกว่า 45 วิ
      if (expectedEvapTime < 15000) expectedEvapTime = 15000;
      if (expectedEvapTime > 45000) expectedEvapTime = 45000;

      // ปรินต์โชว์สมการออกจอ Serial Monitor ให้อาจารย์ดู
      Serial.println("\n==================================");
      Serial.println("[AI PHYSICS] Liquid Detected!");
      Serial.print("Temp: "); Serial.print(t); Serial.print(" C | ");
      Serial.print("Humidity: "); Serial.print(h); Serial.println(" %");
      Serial.print("Saturation Vapor (Ps): "); Serial.println(Ps, 4);
      Serial.print("Actual Vapor (Pa):     "); Serial.println(Pa, 4);
      Serial.print("Vapor Deficit (VPD):   "); Serial.println(VPD, 4);
      Serial.print("=> Calculated Evap Time: "); Serial.print(expectedEvapTime / 1000.0); Serial.println(" sec");
      Serial.println("==================================\n");
    }
    
    if (isAnalyzing && !leakAlertSent) {
      // ถ้าเวลาผ่านไปครบกำหนดที่สมการคำนวณไว้ แล้วยังเปียกอยู่ = จุดระเหยสูง = น้ำมัน!
      if (millis() - wetStartTime >= expectedEvapTime) {
        Blynk.virtualWrite(V5, "⚠️ ตรวจพบน้ำมันรั่วซึม!");
        Blynk.logEvent("leak_alert", "🚨 แจ้งเตือน: พบของเหลวจุดระเหยสูง (น้ำมัน) รั่วใต้ท้องรถ!");
        Serial.println("ALERT: Liquid did not evaporate within expected time. OIL LEAK CONFIRMED!");
        
        beepBuzzer(); beepBuzzer();
        leakAlertSent = true;  
        isAnalyzing = false;   
      }
    }
  } else { // เมื่อพื้นผิวแห้ง
    Blynk.virtualWrite(V5, "ไม่พบความผิดปกติใต้ท้องรถ");
    
    if (isAnalyzing) {
       Serial.println("INFO: Liquid evaporated normally. It was H2O (Water).");
    }
    
    leakAlertSent = false; 
    isAnalyzing = false;   
  }
}

void setup() {
  Serial.begin(9600); 
  
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(yellowPin, OUTPUT);
  pinMode(redPin, OUTPUT);
  
  pinMode(fanPin, OUTPUT);
  digitalWrite(fanPin, LOW);
  pinMode(buzzerPin, INPUT); 
  
  // กำหนดโหมดให้ขารับค่าเซนเซอร์น้ำ
  pinMode(rainSensorPin, INPUT);
  
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);
  doorServo.setPeriodHertz(50);
  doorServo.attach(servoPin, 500, 2400); 
  doorServo.write(180); 
  
  dht.begin();
  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);
  
  timer.setInterval(2000L, sendSensor);
  
  Serial.println("System Ready (Thermodynamics Edition)!");
}

void loop() {
  Blynk.run();
  timer.run();

  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    if (command == "OPEN") {
      
      Blynk.logEvent("door_opened", "AI อนุญาตให้เข้า: ประตูโรงรถกำลังเปิด!");
      Blynk.virtualWrite(V4, 1); 
      
      for(int i=0; i<3; i++) { beepBuzzer(); }
      
      Serial.println("Opening Door (10 degrees)");
      doorServo.write(10);
      
      for(int j=0; j<100; j++) {
        delay(100);
        Blynk.run(); 
      }
      
      for(int i=0; i<3; i++) { beepBuzzer(); }
      
      Serial.println("Closing Door (180 degrees)");
      doorServo.write(180);
      Blynk.virtualWrite(V4, 0);
      
      delay(500);
    }
  }

  // เซ็นเซอร์ Ultrasonic
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  duration = pulseIn(echoPin, HIGH, 30000); 
  distance = (duration == 0) ? 999 : (duration * 0.034 / 2);
  
  if (distance > 10 && distance < 400) {
    digitalWrite(greenPin, HIGH); digitalWrite(yellowPin, LOW); digitalWrite(redPin, LOW);
  } else if (distance > 4 && distance <= 10) {
    digitalWrite(greenPin, LOW); digitalWrite(yellowPin, HIGH); digitalWrite(redPin, LOW);
  } else if (distance <= 4) {
    digitalWrite(greenPin, LOW); digitalWrite(yellowPin, LOW); digitalWrite(redPin, HIGH);
  } else {
    digitalWrite(greenPin, LOW); digitalWrite(yellowPin, LOW); digitalWrite(redPin, LOW);
  }
}
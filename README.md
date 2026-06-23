# 🚘 IoT Smart Garage (ระบบโรงรถอัจฉริยะ)

![Project Status](https://img.shields.io/badge/Status-Completed-success)
![Platform](https://img.shields.io/badge/Platform-ESP32-orange)
![AI](https://img.shields.io/badge/AI-YOLOv8%20%7C%20EasyOCR-blue)
![Cloud](https://img.shields.io/badge/Cloud-Blynk%20%7C%20Telegram-blueviolet)

**IoT Smart Garage** คือโปรเจกต์ระบบโรงจอดรถอัจฉริยะที่บูรณาการเทคโนโลยีคอมพิวเตอร์วิทัศน์ (Computer Vision) เข้ากับระบบอินเทอร์เน็ตของสรรพสิ่ง (IoT) เพื่อยกระดับความสะดวกสบายและความปลอดภัยสูงสุดให้แก่ที่อยู่อาศัย

โปรเจกต์นี้ได้รับการพัฒนาขึ้นโดยนักศึกษาคณะวิศวกรรมศาสตร์ สาขาคอมพิวเตอร์และปัญญาประดิษฐ์ มหาวิทยาลัยหอการค้าไทย (UTCC)

---

## ✨ Key Features (ความสามารถเด่นของระบบ)

* 📷 **AI License Plate Recognition:** ตรวจจับและสแกนป้ายทะเบียนรถยนต์ด้วย YOLOv8 และ EasyOCR หากตรงกับ Whitelist ระบบจะสั่งเปิดประตูโรงรถอัตโนมัติ
* 🚥 **Smart Parking Assist:** ระบบช่วยกะระยะจอดรถด้วยเซนเซอร์ Ultrasonic พร้อมแสดงสถานะผ่านไฟจราจร LED (เขียว, เหลือง, แดง) เพื่อป้องกันอุบัติเหตุ
* 🌡️ **Auto-Ventilation System:** ตรวจวัดอุณหภูมิด้วย DHT11 หากโรงรถมีความร้อนสะสมเกิน 35°C ระบบจะสั่งการ Relay เพื่อเปิดพัดลมระบายอากาศอัตโนมัติ
* 🔬 **Thermodynamic Oil Leak Detection:** นวัตกรรมตรวจจับคราบน้ำมันรั่วซึมใต้ท้องรถ โดยใช้ Rain Drop Sensor ทำงานร่วมกับสมการอุณหพลศาสตร์ (Magnus-Tetens Formula และ Dalton's Law) เพื่อแยกแยะน้ำแอร์รถยนต์ออกจากน้ำมันเครื่อง
* ☁️ **Cloud Logging & Alerts:** * บันทึกประวัติการเข้า-ออก (เวลา/เลขทะเบียน) ลงใน **Google Sheets**
  * แจ้งเตือนแบบ Real-time พร้อมส่งรูปภาพรถผ่าน **Telegram Bot**
  * ควบคุมและติดตามสถานะเซนเซอร์ผ่านแอปพลิเคชัน **Blynk IoT**

---

## 🛠️ Hardware Components (ฮาร์ดแวร์ที่ใช้)

* **Microcontroller:** ESP32 Board
* **Sensors:** * HC-SR04 (Ultrasonic Sensor)
  * DHT11 (Temperature & Humidity Sensor)
  * Rain Drop Sensor (Applied for Oil Leak Detection)
* **Actuators:**
  * SG90 Micro Servo Motor (Door mechanism)
  * 12V Exhaust Fan with 1-Channel Relay Module
  * Traffic Light LED Module
  * Active Buzzer
* **Camera:** 1080P Webcam (for AI Processing)

---

## 💻 Software & Technologies (เทคโนโลยีที่ใช้)

* **Languages:** Python (Computer Vision), C++ (ESP32 Firmware)
* **AI/ML:** YOLOv8 (Object Detection), EasyOCR (Optical Character Recognition)
* **IoT Platform:** Blynk IoT Cloud
* **APIs & Integrations:** Telegram Bot API, Google Forms/Sheets HTTP POST
* **IDE:** Arduino IDE, Visual Studio Code, Google Colab

---

## 🏗️ System Architecture (สถาปัตยกรรมระบบ)

1. **Input / AI Processing:** กล้อง Webcam รับภาพวิดีโอส่งให้สคริปต์ Python ทำการรันโมเดล YOLOv8 และ EasyOCR เพื่อตรวจสอบสิทธิ์
2. **Controller:** หากสิทธิ์ถูกต้อง Python จะส่งคำสั่ง (Serial Communication) ไปยังบอร์ด ESP32 เพื่อขับเคลื่อน Servo Motor
3. **IoT & Cloud:** ESP32 จะคอยอ่านค่าเซนเซอร์ต่างๆ และคำนวณสมการเพื่ออัปเดตสถานะขึ้นแพลตฟอร์ม Blynk ผ่าน Wi-Fi
4. **Logging:** ควบคู่กันนั้น Python จะทำการยิง HTTP Request เพื่อส่งแจ้งเตือนและภาพเข้า Telegram พร้อมลงบันทึกใน Google Sheets

---

## 👥 Contributors (คณะผู้จัดทำ)

นักศึกษาคณะวิศวกรรมศาสตร์ สาขาคอมพิวเตอร์และปัญญาประดิษฐ์ (UTCC)
* นายเฉลิมชัย เจียมเดช (2410711102003)
* นางสาวณภัทร ศรีผ่องใส (2410711102005)
* นายปฏิภาณ น้ำนุช (2410711102016)
* นายภัทธดล โมราขาว (2410711102043)

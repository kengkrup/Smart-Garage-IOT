from flask import Flask, Response
import cv2
import easyocr
from ultralytics import YOLO
import time
import serial
import math
import requests 
from datetime import datetime 
import threading 
import os # [เพิ่มใหม่] นำเข้าไลบรารีสำหรับจัดการไฟล์และโฟลเดอร์

app = Flask(__name__)

# =========================================================
# 1. ตั้งค่าฐานข้อมูลและคลาวด์
# =========================================================
authorized_plates = ["--ใส่ทะเบียนที่อนุญาต--", "--เพิ่มทะเบียนที่อนุญาตได้เรื่อยๆ--"] 

# ⚠️ อย่าลืมใส่ Token ของคุณ
TELEGRAM_TOKEN = "--ใส่โทเคนบอทของคุณที่นี่--"
TELEGRAM_CHAT_ID = "--ใส่ไอดีแชทของคุณที่นี่--"
FORM_URL = "--ใส่ URL ของ Google Form ที่คุณสร้างไว้ที่นี่--"

# --- [เพิ่มใหม่] ตั้งค่าโฟลเดอร์สำหรับเก็บรูป ---
IMG_SAVE_DIR = r"C:\Users\Pathipan\Desktop\AI webcam\Img"

# --- ระบบป้องกันการส่งซ้ำ (Debounce) ---
last_seen_plates = {}
COOLDOWN_SECONDS = 15

# =========================================================
# 2. ฟังก์ชันระบบแจ้งเตือน, บันทึกข้อมูล และลบรูปอัตโนมัติ
# =========================================================
def log_to_google_sheets(plate_text, status):
    now = datetime.now()
    data = {
        "entry.1646569517": now.strftime("%d/%m/%Y"), 
        "entry.1510849411": now.strftime("%H:%M:%S"), 
        "entry.1215036889": plate_text,               
        "entry.923609846": status                     
    }
    try:
        requests.post(FORM_URL, data=data)
        print(f"✅ [Sheets] บันทึกสำเร็จ: {plate_text} ({status})")
    except Exception as e:
        print(f"❌ [Sheets] บันทึกไม่สำเร็จ: {e}")

def send_telegram_alert(image_path, plate_text, status):
    if status == "อนุญาตให้เข้า":
        caption = f"🟢 อนุญาตให้เข้า\n📌 ทะเบียน: {plate_text}\n⏰ เวลา: {datetime.now().strftime('%H:%M:%S')}"
    else:
        caption = f"🔴 ไม่อนุญาต!\n📌 ทะเบียน: {plate_text}\n⏰ เวลา: {datetime.now().strftime('%H:%M:%S')}"
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    try:
        with open(image_path, 'rb') as photo:
            payload = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
            response = requests.post(url, data=payload, files={'photo': photo})
            
            if response.status_code == 200:
                print("📲 [Telegram] แจ้งเตือนสำเร็จ!")
            else:
                print(f"❌ [Telegram] ส่งไม่สำเร็จ! ระบบฟ้องว่า: {response.text}")
    except Exception as e:
        print(f"❌ [Telegram] โค้ดพัง/เน็ตหลุด: {e}")

# --- [เพิ่มใหม่] ฟังก์ชันรอลบรูปภาพ ---
def delete_image_delayed(image_path, delay_seconds):
    time.sleep(delay_seconds) # หน่วงเวลาตามที่กำหนด
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"🗑️ [Auto-Delete] ลบรูปภาพจากเครื่องสำเร็จ: {image_path}")
    except Exception as e:
        print(f"❌ [Auto-Delete] ไม่สามารถลบรูปได้: {e}")

def trigger_cloud_actions(plate_text, status, frame_to_save):
    # ตรวจสอบว่ามีโฟลเดอร์ Img หรือยัง ถ้ายังไม่มีโปรแกรมจะสร้างให้อัตโนมัติ
    if not os.path.exists(IMG_SAVE_DIR):
        os.makedirs(IMG_SAVE_DIR)
        
    # สร้างเส้นทางไฟล์แบบระบุโฟลเดอร์
    img_filename = f"capture_{int(time.time())}.jpg"
    img_path = os.path.join(IMG_SAVE_DIR, img_filename)
    
    cv2.imwrite(img_path, frame_to_save)
    
    # สั่งให้ทำงานเบื้องหลัง
    threading.Thread(target=log_to_google_sheets, args=(plate_text, status)).start()
    threading.Thread(target=send_telegram_alert, args=(img_path, plate_text, status)).start()
    
    # [เพิ่มใหม่] สั่งให้ลบรูปหลังจากผ่านไป 5 นาที (300 วินาที)
    threading.Thread(target=delete_image_delayed, args=(img_path, 300)).start()

# =========================================================
# 3. เชื่อมต่อฮาร์ดแวร์ & AI
# =========================================================
arduino = None
try:
    arduino = serial.Serial('COM12', 9600, timeout=1) 
    time.sleep(2) 
    print("✅ เชื่อมต่อ ESP32 (COM12) สำเร็จ")
except Exception as e:
    print(f"⚠️ ไม่สามารถเชื่อมต่อ COM12 ได้: {e}")
    print("   โปรแกรมจะทำงานต่อโดยไม่มีการสั่ง ESP32")

print("กำลังโหลดโมเดล EasyOCR และ YOLO...")
reader = easyocr.Reader(['th', 'en'])
model = YOLO('best.pt')

print("โหลดเสร็จสิ้น! กำลังเปิดกล้อง...")
cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("❌ ไม่สามารถเปิดกล้องได้! กรุณาตรวจสอบการเชื่อมต่อ")
    exit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

last_read_time = 0

# =========================================================
# 4. ฟังก์ชันประมวลผล AI และปล่อยสัญญาณภาพขึ้นเว็บ
# =========================================================
def generate_frames():
    global last_read_time
    
    while True:
        ret, frame = cap.read()
        
        if not ret or frame is None:
            print("❌ ดึงภาพจากกล้องไม่ได้!")
            time.sleep(2)
            continue

        clean_frame = frame.copy()
        results = model(frame, imgsz=640, verbose=False)
        
        for r in results:
            boxes = r.boxes
            if len(boxes) > 0:
                min_x, min_y = 9999, 9999
                max_x, max_y = 0, 0
                valid_detection = False
                centers = [] 
                
                for box in boxes:
                    confidence = box.conf[0].item()
                    if confidence > 0.2: 
                        valid_detection = True
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        
                        cx = (x1 + x2) // 2
                        cy = (y1 + y2) // 2
                        centers.append((cx, cy))
                        
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
                        
                        min_x = min(min_x, x1)
                        min_y = min(min_y, y1)
                        max_x = max(max_x, x2)
                        max_y = max(max_y, y2)
                
                if valid_detection:
                    padding_x = 40
                    padding_y = 15
                    min_x = max(0, min_x - padding_x)
                    min_y = max(0, min_y - padding_y)
                    max_x = min(frame.shape[1], max_x + padding_x)
                    max_y = min(frame.shape[0], max_y + padding_y)
                    
                    cv2.rectangle(frame, (min_x, min_y), (max_x, max_y), (0, 0, 255), 3)
                    
                    current_time = time.time()
                    if current_time - last_read_time > 4:
                        print("\n[YOLO] ตรวจพบป้ายทะเบียน! กำลังประมวลผล...")
                        
                        cropped_img = clean_frame[min_y:max_y, min_x:max_x]
                        
                        if cropped_img.size > 0: 
                            centers = sorted(centers, key=lambda p: p[0])
                            angle = 0
                            
                            if len(centers) >= 2:
                                dx = centers[-1][0] - centers[0][0]
                                dy = centers[-1][1] - centers[0][1]
                                angle = math.degrees(math.atan2(dy, dx))
                                
                            if abs(angle) > 2:
                                h, w = cropped_img.shape[:2]
                                center_pt = (w // 2, h // 2)
                                M = cv2.getRotationMatrix2D(center_pt, angle, 1.0)
                                final_crop = cv2.warpAffine(cropped_img, M, (w, h), borderValue=(255, 255, 255))
                            else:
                                final_crop = cropped_img
                            
                            # --- เริ่มระบบอ่านป้ายและกรองขยะ ---
                            ocr_results = reader.readtext(final_crop)
                            
                            all_text = ""
                            for (bbox, text, prob) in ocr_results:
                                if prob > 0.4:
                                    clean_text = text.replace(" ", "").replace("\n", "").strip()
                                    clean_text = clean_text.replace("กรุงเทพมหานคร", "").replace("กรุงเทพฯ", "")
                                    clean_text = "".join(e for e in clean_text if e.isalnum()) 
                                    all_text += clean_text
                            
                            if len(all_text) < 3:
                                if len(all_text) > 0:
                                    print(f"🗑️ มองข้ามข้อความขยะ/สั้นเกินไป: '{all_text}'")
                            else:
                                print(f"🔍 AI อ่านข้อความรวมได้: '{all_text}'")
                                is_allowed = False
                                matched_plate = ""
                                
                                for plate in authorized_plates:
                                    if plate in all_text:
                                        is_allowed = True
                                        matched_plate = plate
                                        break
                                
                                eval_plate = matched_plate if is_allowed else all_text
                                current_time_sec = time.time()
                                
                                if eval_plate in last_seen_plates and (current_time_sec - last_seen_plates[eval_plate] < COOLDOWN_SECONDS):
                                    print(f"⏳ ข้ามการทำงาน: ทะเบียน '{eval_plate}' เพิ่งสแกนไปเมื่อกี้นี้")
                                else:
                                    last_seen_plates[eval_plate] = current_time_sec
                                    
                                    if is_allowed:
                                        print(f"🟢 [อนุญาตให้เข้า!] ทะเบียนตรงกับ: {matched_plate}")
                                        cv2.putText(frame, "ACCESS GRANTED", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)
                                        
                                        if arduino:
                                            print("--> [ส่งคำสั่ง OPEN ไปที่ ESP32]")
                                            arduino.write(b'OPEN\n') 
                                            
                                        trigger_cloud_actions(matched_plate, "อนุญาตให้เข้า", clean_frame)
                                        
                                    else:
                                        print(f"🔴 [ไม่อนุญาต] ไม่มีในระบบ")
                                        cv2.putText(frame, "ACCESS DENIED", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)
                                        trigger_cloud_actions(all_text, "ไม่อนุญาต", clean_frame)
                        
                        last_read_time = current_time

        ret_encode, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    print("\n🚀 สตาร์ทเซิร์ฟเวอร์กล้องแล้ว!")
    app.run(host='0.0.0.0', port=5000, threaded=True)
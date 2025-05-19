# utils/coin_detector.py
from ultralytics import YOLO
import cv2

# Load the YOLOv8 model
model = YOLO("app/models/coin/best.pt")

def detect_coin(image):
    results = model(image)
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            return (x1, y1, x2, y2), conf
    return None, None

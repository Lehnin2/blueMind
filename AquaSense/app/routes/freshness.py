from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import torch
from PIL import Image
import cv2
import numpy as np
import io
import os
from ultralytics import YOLO
from pathlib import Path
import base64

router = APIRouter()

# Paramètres
freshness_classes = ['fresh', 'rotten']
model_path = Path('model/besties.pt')
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Charger le modèle
model = YOLO(model_path)

def predict_image_yolo(image_bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_np = np.array(img)

    # Détection sur l'image entière
    results = model.predict(img_np, conf=0.25, device="cpu", verbose=False)
    detections = results[0].boxes

    # Annoter l'image
    annotated_img = img_np.copy()
    freshness_detected = []
    confidences = []

    for box in detections:
        cls_id = int(box.cls.item())
        conf = box.conf.item()
        label = freshness_classes[cls_id]

        xyxy = box.xyxy.cpu().numpy().astype(int)[0]

        # Dessiner un rectangle vert pour fresh, rouge pour rotten
        color = (0, 255, 0) if label == 'fresh' else (0, 0, 255)
        cv2.rectangle(annotated_img, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), color, 2)
        
        # Afficher uniquement "Fresh" ou "Non-Fresh"
        display_text = "Fresh" if label == 'fresh' else "Non-Fresh"
        cv2.putText(annotated_img, display_text, (xyxy[0], xyxy[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        freshness_detected.append(label)
        confidences.append(conf)

    # Retourner le résultat le plus probable
    if freshness_detected:
        max_conf_idx = np.argmax(confidences)
        result_class = freshness_detected[max_conf_idx]
        return {
            "class": "Fresh" if result_class == 'fresh' else "Non-Fresh",
            "confidence": confidences[max_conf_idx],
            "annotated_image": base64.b64encode(cv2.imencode('.jpg', annotated_img)[1]).decode()
        }
    else:
        return {
            "class": "Unknown",
            "confidence": 0.0,
            "annotated_image": base64.b64encode(cv2.imencode('.jpg', img_np)[1]).decode()
        }

def analyze_video(video_path, conf_threshold=0.25):
    cap = cv2.VideoCapture(video_path)
    class_counts = {cls: 0 for cls in freshness_classes}
    frames = []
    frame_count = 0
    max_frames = 30  # Limiter le nombre de frames pour éviter les problèmes de mémoire

    while cap.isOpened() and frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        try:
            # Redimensionner la frame pour un traitement plus rapide
            frame = cv2.resize(frame, (640, 480))
            
            # Effectuer la détection
            results = model.predict(frame, conf=conf_threshold, device="cpu", verbose=False)
            detections = results[0].boxes

            # Annoter la frame
            annotated_frame = frame.copy()
            for box in detections:
                cls_id = int(box.cls.item())
                conf = box.conf.item()
                label = freshness_classes[cls_id]
                class_counts[label] += 1

                xyxy = box.xyxy.cpu().numpy().astype(int)[0]
                
                # Dessiner un rectangle vert pour fresh, rouge pour rotten
                color = (0, 255, 0) if label == 'fresh' else (0, 0, 255)
                cv2.rectangle(annotated_frame, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), color, 2)
                
                # Afficher uniquement "Fresh" ou "Non-Fresh"
                display_text = "Fresh" if label == 'fresh' else "Non-Fresh"
                cv2.putText(annotated_frame, display_text, (xyxy[0], xyxy[1] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # Ajouter la frame annotée à la liste
            frames.append(annotated_frame)
            frame_count += 1

        except Exception as e:
            print(f"Erreur lors de la détection vidéo : {e}")

    cap.release()

    # Trouver la classe dominante
    result_class = max(class_counts, key=class_counts.get)
    
    # Convertir les frames en base64
    encoded_frames = []
    for frame in frames:
        _, buffer = cv2.imencode('.jpg', frame)
        encoded_frames.append(base64.b64encode(buffer).decode())

    return {
        "class": "Fresh" if result_class == 'fresh' else "Non-Fresh",
        "counts": class_counts,
        "frames": encoded_frames
    }

@router.post("/classify")
async def classify_freshness(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Aucun fichier sélectionné")

    try:
        contents = await file.read()
        result = predict_image_yolo(contents)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse : {str(e)}")

@router.post("/classify-video")
async def classify_video_freshness(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Aucun fichier sélectionné")

    try:
        # Sauvegarder temporairement la vidéo
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # Analyser la vidéo
        result = analyze_video(temp_path)

        # Supprimer le fichier temporaire
        os.remove(temp_path)

        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse : {str(e)}") 
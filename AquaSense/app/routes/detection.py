import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from io import BytesIO
import cv2
from ultralytics import YOLO
from starlette.requests import Request
import tempfile
import numpy as np
import time

# Charger le modèle YOLO
model_yolo = YOLO("model/best.pt")


# Dossier des uploads
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialisation des templates
templates = Jinja2Templates(directory="templates")

# Créer un router pour les routes liées à la détection
router = APIRouter()

# Fonction pour vérifier les extensions autorisées
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {
        'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'wmv'  # Ajout des formats vidéo
    }

# Fonction pour la prédiction avec YOLO
def predict_media_yolo(model, file_path, conf_threshold=0.25):
    try:
        # Vérifier si c'est une vidéo
        if file_path.lower().endswith(('.mp4', '.avi', '.mov', '.wmv')):
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return None, []

            # Obtenir les propriétés de la vidéo
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))

            # Créer le fichier de sortie
            output_path = os.path.join(UPLOAD_FOLDER, 'output_' + os.path.basename(file_path))
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

            detections = []
            frame_count = 0

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # Traiter toutes les frames pour une meilleure détection
                results = model(frame, conf=conf_threshold)
                
                for r in results:
                    for box in r.boxes:
                        conf = float(box.conf.item())
                        if conf >= conf_threshold:
                            label = model.names[int(box.cls.item())]
                            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                            
                            # Ajouter la détection avec les coordonnées
                            detections.append({
                                "class": label,
                                "confidence": conf,
                                "bbox": [x1, y1, x2, y2]
                            })

                            # Dessiner les bounding boxes
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                            text = f"{label} {conf:.2f}"
                            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
                            cv2.rectangle(frame, (x1, y1-text_size[1]-10), (x1+text_size[0], y1), (0, 0, 0), -1)
                            cv2.putText(frame, text, (x1, y1-10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

                out.write(frame)
                frame_count += 1

            cap.release()
            out.release()
            return output_path, detections

        else:
            # Traitement des images
            image = cv2.imread(file_path)
            if image is None:
                return None, []

            results = model(image, conf=conf_threshold)
            detections = []

            for r in results:
                for box in r.boxes:
                    conf = float(box.conf.item())
                    if conf >= conf_threshold:
                        label = model.names[int(box.cls.item())]
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        
                        # Ajouter la détection avec les coordonnées
                        detections.append({
                            "class": label,
                            "confidence": conf,
                            "bbox": [x1, y1, x2, y2]
                        })

                        # Dessiner les bounding boxes
                        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 3)
                        text = f"{label} {conf:.2f}"
                        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
                        cv2.rectangle(image, (x1, y1-text_size[1]-10), (x1+text_size[0], y1), (0, 0, 0), -1)
                        cv2.putText(image, text, (x1, y1-10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

            result_path = os.path.join(UPLOAD_FOLDER, os.path.basename(file_path))
            cv2.imwrite(result_path, image)
            return result_path, detections

    except Exception as e:
        return None, []

# Mise à jour de la route d'upload
@router.post("/detect")
async def detect_image(file: UploadFile = File(...), model_type: str = "general"):
    if file.filename == '':
        raise HTTPException(status_code=400, detail="Aucun fichier sélectionné")

    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Format de fichier non autorisé")

    # Sauvegarder le fichier téléchargé
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Sélectionner le modèle en fonction du type
    selected_model = model_mediterranean if model_type == "mediterranean" else model_yolo
    
    # Prédiction avec le modèle sélectionné
    result_path_yolo, detections = predict_media_yolo(selected_model, file_path, 0.2)
    if result_path_yolo is None:
        raise HTTPException(status_code=500, detail="Erreur de traitement avec le modèle")

    return {
        "image_url": f"/static/uploads/{os.path.basename(result_path_yolo)}",
        "detections": detections
    }

@router.post('/detect-video')
async def detect_video(file: UploadFile = File(...)):
    try:
        # Vérifier que le fichier est une vidéo
        if not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="Le fichier doit être une vidéo")
        
        # Créer un fichier temporaire pour la vidéo
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Ouvrir la vidéo
        cap = cv2.VideoCapture(temp_file_path)
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Impossible d'ouvrir la vidéo")
        
        # Obtenir les propriétés de la vidéo
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        # Créer un fichier temporaire pour la vidéo de sortie
        output_path = temp_file_path + '_output.mp4'
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Traiter chaque frame
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Analyser la frame avec YOLO
            results = model_yolo(frame, conf=0.2)
            
            # Dessiner les bounding boxes
            for r in results:
                for box in r.boxes:
                    conf = float(box.conf.item())
                    if conf >= 0.2:  # Seuil de confiance
                        label = model_yolo.names[int(box.cls.item())]
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        
                        # Déterminer la couleur en fonction de la classe
                        color = (0, 255, 0)  # Vert par défaut
                        if label in ['poisonous', 'venomous']:
                            color = (0, 0, 255)  # Rouge pour les poissons dangereux
                        
                        # Dessiner le rectangle avec un fond semi-transparent
                        overlay = frame.copy()
                        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
                        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
                        
                        # Dessiner la bordure
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        
                        # Ajouter le texte
                        text = f"{label.upper()} {conf:.1%}"
                        cv2.putText(frame, text, (x1, y1 - 10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Écrire la frame traitée
            out.write(frame)
            frame_count += 1
            
            # Libérer la mémoire
            del frame
        
        # Libérer les ressources
        cap.release()
        out.release()
        
        # Lire la vidéo traitée
        with open(output_path, 'rb') as f:
            video_bytes = f.read()
        
        # Supprimer les fichiers temporaires
        os.unlink(temp_file_path)
        os.unlink(output_path)
        
        # Renvoyer la vidéo traitée
        return StreamingResponse(
            BytesIO(video_bytes),
            media_type="video/mp4",
            headers={"Content-Disposition": "attachment; filename=detected_video.mp4"}
        )
        
    except Exception as e:
        # Nettoyer les fichiers temporaires en cas d'erreur
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        if 'output_path' in locals() and os.path.exists(output_path):
            os.unlink(output_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect-ar")
async def detect_ar(file: UploadFile = File(...)):
    if file.filename == '':
        raise HTTPException(status_code=400, detail="Aucun fichier sélectionné")

    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Format de fichier non autorisé")

    # Sauvegarder le fichier téléchargé
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Prédiction avec YOLO
    result_path_yolo, detections = predict_media_yolo(model_yolo, file_path, 0.2)
    if result_path_yolo is None:
        raise HTTPException(status_code=500, detail="Erreur de traitement avec YOLO")

    return {
        "detections": detections
    }

@router.get("/ar", response_class=HTMLResponse)
async def detection_ar_page(request: Request):
    return templates.TemplateResponse(
        "detection_ar.html",
        {"request": request, "title": "Détection AR - Blue Mind"}
    )

# Route for the detection page - remove the /detection prefix since it's already in the router
@router.get("/", response_class=HTMLResponse)
async def detection_page(request: Request):
    return templates.TemplateResponse("detection.html", {"request": request})

@router.post("/analyze/")
async def analyze_frame(file: UploadFile = File(...)):
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Format de fichier non autorisé")

    # Sauvegarder le fichier temporairement
    temp_path = os.path.join(UPLOAD_FOLDER, "temp_" + file.filename)
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    try:
        # Analyse avec YOLO
        image = cv2.imread(temp_path)
        results = model_yolo(image, conf=0.2)
        
        detections = []
        for r in results:
            for box in r.boxes:
                conf = float(box.conf.item())
                if conf >= 0.2:
                    label = model_yolo.names[int(box.cls.item())]
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    detections.append({
                        "label": label,
                        "confidence": conf,
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2
                    })

        # Nettoyer le fichier temporaire
        os.remove(temp_path)
        
        return {"detections": detections}
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

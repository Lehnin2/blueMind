from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import io
import os
import logging
import cv2
import numpy as np
import tempfile
import base64

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Paramètres généraux
class_names = ['electric', 'poisonous', 'venomous']
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_path = os.path.join("model", "poisson_classifier.pth")

# Vérifier si le modèle existe
if not os.path.exists(model_path):
    logger.error(f"Le modèle n'a pas été trouvé à l'emplacement: {model_path}")
    raise FileNotFoundError(f"Le modèle n'a pas été trouvé à l'emplacement: {model_path}")

# Transformations
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                        [0.229, 0.224, 0.225])
])

# Charger le modèle
def load_model():
    try:
        logger.info("Chargement du modèle...")
        model = models.mobilenet_v2(pretrained=False)
        num_ftrs = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(num_ftrs, len(class_names))
        model.load_state_dict(torch.load(model_path, map_location=device))
        model.to(device)
        model.eval()
        logger.info("Modèle chargé avec succès")
        return model
    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle: {str(e)}")
        raise

try:
    model = load_model()
except Exception as e:
    logger.error(f"Impossible de charger le modèle: {str(e)}")
    raise

def predict_image(image):
    try:
        input_tensor = transform(image).unsqueeze(0).to(device)
        with torch.no_grad():
            output = model(input_tensor)
            probs = torch.softmax(output[0], dim=0)
            confidence, predicted_idx = torch.max(probs, 0)
        return class_names[predicted_idx.item()], confidence.item(), probs.cpu().numpy()
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction: {str(e)}")
        raise

@router.post("/classify")
async def classify_fish(file: UploadFile = File(...)):
    try:
        logger.info("Début de la classification...")
        
        # Vérifier le type de fichier
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Le fichier doit être une image")
        
        # Lire l'image
        contents = await file.read()
        try:
            image = Image.open(io.BytesIO(contents)).convert("RGB")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Impossible de lire l'image: {str(e)}")
        
        # Faire la prédiction
        try:
            predicted_class, confidence, probs = predict_image(image)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors de la prédiction: {str(e)}")
        
        # Préparer la réponse
        result = {
            "class": predicted_class,
            "confidence": confidence,
            "probabilities": {
                class_name: float(prob) for class_name, prob in zip(class_names, probs)
            }
        }
        
        logger.info(f"Classification réussie: {result['class']} (confiance: {result['confidence']:.2f})")
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la classification: {str(e)}")

@router.post("/analyze-video")
async def analyze_video(file: UploadFile = File(...)):
    try:
        logger.info("Début de l'analyse vidéo...")
        
        # Vérifier le type de fichier
        if not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="Le fichier doit être une vidéo")
        
        # Sauvegarder la vidéo temporairement
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            contents = await file.read()
            temp_file.write(contents)
            video_path = temp_file.name
        
        try:
            # Analyser la vidéo
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise HTTPException(status_code=400, detail="Impossible d'ouvrir la vidéo")
                
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            class_confidence_sum = {cls: 0.0 for cls in class_names}
            valid_prediction_count = 0
            sample_every_n = 30  # Analyser une frame toutes les 30 frames
            threshold = 0.7

            for frame_idx in range(total_frames):
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_idx % sample_every_n == 0:
                    try:
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        pil_image = Image.fromarray(rgb_frame)
                        predicted_class, confidence, _ = predict_image(pil_image)

                        if confidence >= threshold:
                            class_confidence_sum[predicted_class] += confidence
                            valid_prediction_count += 1
                    except Exception as e:
                        logger.warning(f"Erreur frame {frame_idx}: {e}")

            cap.release()
            os.unlink(video_path)  # Supprimer le fichier temporaire

            if valid_prediction_count == 0:
                raise HTTPException(status_code=400, detail="Aucune prédiction valide dans la vidéo")
            
            # Calculer les probabilités moyennes
            best_class = max(class_confidence_sum, key=class_confidence_sum.get)
            total_confidence = sum(class_confidence_sum.values())
            probabilities = {
                cls: conf / total_confidence if total_confidence > 0 else 0
                for cls, conf in class_confidence_sum.items()
            }
            
            result = {
                "class": best_class,
                "confidence": class_confidence_sum[best_class] / valid_prediction_count,
                "probabilities": probabilities
            }
            
            logger.info(f"Analyse vidéo réussie: {result['class']} (confiance: {result['confidence']:.2f})")
            return JSONResponse(content=result)
            
        except Exception as e:
            if os.path.exists(video_path):
                os.unlink(video_path)
            raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse vidéo: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse vidéo: {str(e)}")
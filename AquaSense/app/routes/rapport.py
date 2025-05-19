from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
import pathlib
import base64
from PIL import Image, ImageDraw
import google.generativeai as genai

# Create router with explicit prefix and tags
router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Configuration du dossier des uploads
UPLOAD_FOLDER = 'static/images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configuration de l'API Gemini
API_KEY = "AIzaSyCTCQYmhuKqBQAeKwByP23KijqON98m91k"
genai.configure(api_key=API_KEY)
MODEL_NAME = "gemini-1.5-flash"  # Utilisez un modèle plus récent

@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("rapport.html", {"request": request, "title": "Rapport"})

@router.get("/rapport")
async def rapport_index(request: Request):
    return templates.TemplateResponse("rapport.html", {"request": request})

@router.post("/generate-image")
async def generate_image(prompt: str = Form(...)):
    if not prompt:
        raise HTTPException(status_code=400, detail="Veuillez fournir un prompt")

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        
        # Génération avec explicitement la demande d'image
        response = model.generate_content(
            [
                f"Génère un rapport détaillé sur: {prompt}. ",
                "Inclure une image réaliste et des sections pour: ",
                "1. Caractéristiques physiques\n",
                "2. Habitat et mode de vie\n",
                "3. Reproduction\n",
                "4. Alimentation\n",
                "5. Importance écologique\n",
                "6. Importance économique",
                "Format Markdown avec ## Titres"
            ]
        )
        
        text_content = response.text
        image_data = None
        image_path = None

        # Vérifier si la réponse contient des images
        if response._result.candidates and response._result.candidates[0].content.parts:
            for part in response._result.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    # Sauvegarde de l'image
                    image_binary = part.inline_data.data
                    image_filename = f"generated_{len(os.listdir(UPLOAD_FOLDER))}.png"
                    image_path = os.path.join(UPLOAD_FOLDER, image_filename)
                    pathlib.Path(image_path).write_bytes(image_binary)
                    
                    # Encodage base64 pour affichage direct
                    encoded_image = base64.b64encode(image_binary).decode('utf-8')
                    image_data = f"data:image/png;base64,{encoded_image}"
                    image_path = f"images/{image_filename}"  # Chemin relatif pour le frontend
                    break  # On prend la première image trouvée

        return JSONResponse({
            "text": text_content,
            "image_data": image_data,
            "image_path": image_path
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de génération: {str(e)}")
@router.get("/fishing-tips")
async def fishing_tips():
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(
            "Génère un guide de bonnes pratiques pour pêcher en Tunisie "
            "avec des conseils détaillés et des images. Format Markdown."
        )
        
        result = {"text": response.text, "images": []}
        
        # Traitement des images si disponibles
        if hasattr(response, '_result') and response._result.candidates:
            for part in response._result.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_binary = part.inline_data.data
                    image_filename = f"fishing_{len(os.listdir(UPLOAD_FOLDER))}.png"
                    image_path = os.path.join(UPLOAD_FOLDER, image_filename)
                    pathlib.Path(image_path).write_bytes(image_binary)
                    result["images"].append(f"images/{image_filename}")
        
        return JSONResponse(result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/placeholder/{width}/{height}")
async def get_placeholder(width: int, height: int):
    try:
        # Créer une nouvelle image avec un fond bleu
        img = Image.new('RGB', (width, height), color='#176B87')
        draw = ImageDraw.Draw(img)

        # Ajouter le texte montrant les dimensions
        text = f'{width}x{height}'
        # Calculer la position du texte (centre)
        text_bbox = draw.textbbox((0, 0), text)
        text_x = (width - (text_bbox[2] - text_bbox[0])) // 2
        text_y = (height - (text_bbox[3] - text_bbox[1])) // 2
        
        # Dessiner le texte
        draw.text((text_x, text_y), text, fill='white')
        
        # Sauvegarder l'image
        img_path = os.path.join(UPLOAD_FOLDER, f'placeholder_{width}x{height}.png')
        img.save(img_path)
        
        return FileResponse(img_path, media_type="image/png")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
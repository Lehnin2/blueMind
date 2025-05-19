from fastapi import FastAPI, Request, Form, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import cv2
import json
from pathlib import Path
import uvicorn

# Blue Mind Fishing App routes
from app.routes import meteo
from app.routes import detection
from app.routes import chatbot
from app.routes import auth
from app.routes import fish_classification
from app.routes import freshness
from app.routes import rapport
from app.middleware.auth_middleware import auth_middleware
from config.settings import HOST, PORT, DEBUG

# Additional modules from the Fish Detection/Maritime app
from app.api.routes import router as api_router
from app.core.models import initialize_models

# Custom utilities from Fish Detection app
from app.utils.predictor import get_predictor, run_prediction
from app.utils.weight_predictor import predict_weight
from app.utils.fish_info import get_fish_info
from maritime_watch import run_maritime_watch, get_categories

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="Blue Mind Fishing App",
    description="Application d'assistance à la pêche avec détection de poissons et analyse maritime",
    version="1.0.0"
)

# Ajout du middleware d'authentification
app.middleware("http")(auth_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up static and templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Initialize predictor for fish detection
predictor = get_predictor()

# Store maritime notification globally
latest_notification = {"content": "", "type": "info"}

# --------------------
# Startup
# --------------------
@app.on_event("startup")
async def startup_event():
    initialize_models()

# Include API router for vector similarity + LLM
app.include_router(api_router)

# --------------------
# Original Blue Mind routes
# --------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "title": "Blue Mind - Votre Assistant de Pêche"})

@app.get("/index", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Espace Pêcheur"})

@app.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page(request: Request):
    return templates.TemplateResponse("chatbot.html", {"request": request, "title": "Assistant de Pêche"})

@app.get("/fish-classification", response_class=HTMLResponse)
async def fish_classification_page(request: Request):
    return templates.TemplateResponse("fish_classification.html", {"request": request, "title": "Classification des Poissons Toxiques"})

@app.get("/freshness-detection", response_class=HTMLResponse)
async def freshness_detection_page(request: Request):
    return templates.TemplateResponse("freshness-detection.html", {"request": request, "title": "Détection de Fraîcheur"})

@app.get("/explorateur-marin", response_class=HTMLResponse)
async def explorateur_marin_page(request: Request):
    return templates.TemplateResponse("rapport.html", {"request": request, "title": "Explorateur Marin Tunisien"})

# Include original Blue Mind routes
app.include_router(meteo.router, prefix="/meteo", tags=["meteo"])
app.include_router(detection.router, prefix="/detection", tags=["detection"])
app.include_router(chatbot.router, prefix="/chatbot", tags=["chatbot"])
app.include_router(auth.router, tags=["auth"])
app.include_router(fish_classification.router, prefix="/fish", tags=["fish"])
app.include_router(freshness.router, prefix="/fish/freshness", tags=["freshness"])
app.include_router(rapport.router)

# --------------------
# Fish Detection Routes (Newly Integrated)
# --------------------
@app.get("/fish_detect", response_class=HTMLResponse)
async def form_page(request: Request):
    return templates.TemplateResponse("fish_measure.html", {
        "request": request,
        "result_img": None,
        "fish_length_cm": None,
        "predicted_weight": None
    })

@app.post("/fish_detect", response_class=HTMLResponse)
async def detect_fish(request: Request, image: UploadFile = File(...)):
    filename = image.filename
    input_path = os.path.join(UPLOAD_DIR, filename)
    result_path = os.path.join(UPLOAD_DIR, "result_" + filename)

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    result_img, length_mm = run_prediction(predictor, input_path, return_length_mm=True)
    length_cm = round(length_mm / 10, 2) if length_mm else None
    cv2.imwrite(result_path, result_img)

    return templates.TemplateResponse("fish_measure.html", {
        "request": request,
        "result_img": "result_" + filename,
        "fish_length_cm": length_cm,
        "predicted_weight": None,
        "input_img": filename
    })

@app.post("/predict_weight", response_class=HTMLResponse)
async def predict_weight_view(request: Request,
                             species: str = Form(...),
                             length: float = Form(...),
                             result_img: str = Form(...),
                             input_img: str = Form(...)):
    try:
        weight = round(predict_weight(length, species), 2)
        
        # Await the async get_fish_info function
        fish_info = await get_fish_info(species, length, weight)
        
    except Exception as e:
        weight = None
        fish_info = {
            "error": str(e),
            "average_length_cm": None,
            "average_weight_kg": None,
            "minimum_legal_size_cm": None,
            "should_release": False,
            "comparison": "Error retrieving data."
        }

    return templates.TemplateResponse("fish_measure.html", {
        "request": request,
        "result_img": result_img,
        "input_img": input_img,
        "fish_length_cm": length,
        "predicted_weight": weight,
        "species": species,
        "fish_info": fish_info
    })

@app.post("/save_location")
async def save_location(request: Request,
                        species: str = Form(...),
                        length: float = Form(...),
                        weight: float = Form(...),
                        lat: float = Form(...),
                        lng: float = Form(...)):
    data_file = "data/catches.json"
    os.makedirs("data", exist_ok=True)

    if os.path.exists(data_file):
        with open(data_file, "r") as f:
            try:
                all_data = json.load(f)
            except json.JSONDecodeError:
                all_data = []
    else:
        all_data = []

    existing = next((entry for entry in all_data if entry["species"] == species), None)
    if existing:
        if weight > existing["weight"] or (weight == existing["weight"] and length > existing["length"]):
            existing.update({
                "length": length,
                "weight": weight,
                "lat": lat,
                "lng": lng
            })
    else:
        all_data.append({
            "species": species,
            "length": length,
            "weight": weight,
            "lat": lat,
            "lng": lng
        })

    with open(data_file, "w") as f:
        json.dump(all_data, f, indent=2)

    return RedirectResponse(url="/map", status_code=302)

@app.get("/map", response_class=HTMLResponse)
async def map_summary(request: Request):
    data_file = "data/catches.json"
    if os.path.exists(data_file):
        with open(data_file, "r") as f:
            all_data = json.load(f)
    else:
        all_data = []

    best_catches = {}
    for entry in all_data:
        sp = entry["species"]
        if sp not in best_catches or entry["weight"] > best_catches[sp]["weight"]:
            best_catches[sp] = entry

    return templates.TemplateResponse("map.html", {
        "request": request,
        "catches": list(best_catches.values())
    })

# --------------------
# LLM Fish Info Route
# --------------------
@app.get("/fish-info", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("fish_lokkup.html", {"request": request})

# --------------------
# Maritime Routes
# --------------------
@app.get("/maritime", response_class=HTMLResponse)
async def maritime_home(request: Request):
    categories = get_categories()
    return templates.TemplateResponse("marine_notif.html", {
        "request": request,
        "categories": categories
    })

@app.post("/run_maritime_watch")
async def start_maritime_watch(background_tasks: BackgroundTasks, category: str = Form("1")):
    background_tasks.add_task(process_maritime_watch, category)
    return {"status": "success", "message": "Maritime watch process started in background"}

@app.get("/notification")
async def get_notification():
    return latest_notification

async def process_maritime_watch(category: str):
    global latest_notification
    latest_notification = {
        "content": f"Processing maritime data for {get_categories()[category]}...",
        "type": "info"
    }

    try:
        result = await run_maritime_watch(category)
        if result["status"] == "success":
            latest_notification = {
                "content": result["notification"],
                "type": "success"
            }
        else:
            latest_notification = {
                "content": f"Error: {result['error']}",
                "type": "error"
            }
    except Exception as e:
        latest_notification = {
            "content": f"Error: {str(e)}",
            "type": "error"
        }

@app.get("/research/{task_type}")
async def get_research(task_type: str):
    try:
        filepath = Path(f"{task_type}_conditions.md")
        if not filepath.exists():
            return JSONResponse(status_code=404, content={"error": f"Research for {task_type} not found"})
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/summary")
async def get_summary():
    try:
        filepath = Path("maritime_notification.txt")
        if not filepath.exists():
            return JSONResponse(status_code=404, content={"error": "Summary notification not found"})
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# --------------------
# Add navigation links to new features
# --------------------
@app.get("/fish-measurement", response_class=HTMLResponse)
async def fish_measurement_page(request: Request):
    return templates.TemplateResponse("fish_measure.html", {"request": request, "title": "Mesure de Poisson"})

@app.get("/maritime-watch", response_class=HTMLResponse)
async def maritime_home(request: Request):
    categories = get_categories()
    return templates.TemplateResponse("marine_notif.html", {
        "request": request,
        "categories": categories
    })

# --------------------
# Uvicorn Runner
# --------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=DEBUG)
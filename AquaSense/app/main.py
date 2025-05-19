from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.routes import fish_detector, poisson_toxique, detection, fish_classification, freshness

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(fish_detector.router, prefix="/fish-detector")
app.include_router(poisson_toxique.router, prefix="/poisson-toxique")
app.include_router(detection.router)
app.include_router(fish_classification.router)
app.include_router(freshness.router)

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/fish-detector")
async def fish_detector_page(request: Request):
    return templates.TemplateResponse("fish_detector.html", {"request": request})

@app.get("/poisson-toxique")
async def poisson_toxique_page(request: Request):
    return templates.TemplateResponse("poisson_toxique.html", {"request": request})

@app.get("/freshness-detection")
async def freshness_detection_page(request: Request):
    return templates.TemplateResponse("freshness-detection.html", {"request": request})

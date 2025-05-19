from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.services.weather_service import WeatherService
import traceback

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def meteo_page(request: Request):
    return templates.TemplateResponse(
        "meteo.html",
        {"request": request, "title": "Météo - Blue Mind"}
    )

@router.get("/current/{coordinates}")
async def get_current_weather(coordinates: str):
    try:
        print(f"Tentative de récupération de la météo pour les coordonnées: {coordinates}")
        weather = await WeatherService.get_current_weather(coordinates)
        if not weather:
            raise HTTPException(status_code=404, detail="Weather data not found")
        return weather
    except Exception as e:
        print(f"Erreur détaillée: {str(e)}")
        print(f"Traceback complet: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/forecast/{coordinates}")
async def get_forecast(coordinates: str, days: int = 3):
    try:
        print(f"Tentative de récupération des prévisions pour les coordonnées: {coordinates}")
        forecast = await WeatherService.get_forecast(coordinates, days)
        if not forecast:
            raise HTTPException(status_code=404, detail="Forecast data not found")
        return forecast
    except Exception as e:
        print(f"Erreur détaillée: {str(e)}")
        print(f"Traceback complet: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import os
import cv2
import numpy as np
from typing import List, Dict
import folium
import pyttsx3
import google.generativeai as genai
from transformers import pipeline
import requests

# Setup templates
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Initialize text-to-speech engine
tts_engine = pyttsx3.init()

# Configure Gemini
GEMINI_API_KEY = "AIzaSyDfjH7tyLkSA6UKhBk1W2VI5oT4X7eyC1E"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Initialize simpler NLP pipelines
text_classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-base",  # Smaller, public model
)

ner_model = pipeline(
    "ner",
    model="dbmdz/bert-large-cased-finetuned-conll03-english",  # Same public NER model
    aggregation_strategy="simple"
)

# Create router
router = APIRouter()

# Define image paths
image_paths = {
    "light_blue": os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools", "carte", "carte_tunisie_bleu.PNG"),
    "blue": os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools", "carte", "carte_tunisie_bleu_foncee.PNG"),
    "green": os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools", "carte", "carte_true_gulf_tunis.PNG"),
    "purple": os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools", "carte", "carte_tunisie_mauve.PNG"),
    "orange": os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools", "carte", "carte_true_gulf_gabes.PNG"),
    "three_zone": os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools", "carte", "carte_trois_bleu_tunisie.PNG")
}

# Zone checking functions
def check_zone_generic(lat: float, lon: float, image_path: str, color_lower: tuple, color_upper: tuple, zone_name: str, restriction: str) -> str:
    if not os.path.exists(image_path):
        return f"Error checking {zone_name} zone: Warning: Image not found."
    try:
        img = cv2.imread(image_path)
        if img is None:
            return f"Error checking {zone_name} zone: Failed to load image."
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mask = cv2.inRange(img_rgb, color_lower, color_upper)
        height, width = img.shape[:2]
        x = int((lon - 7.5) / (12.5 - 7.5) * width)
        y = int((38.5 - lat) / (38.5 - 33.5) * height)
        if 0 <= x < width and 0 <= y < height:
            if mask[y, x] > 0:
                return f"❌ Restricted for {restriction}."
            return f"✅ Allowed for {restriction}."
        return f"Error checking {zone_name} zone: Coordinates out of bounds."
    except Exception as e:
        return f"Error checking {zone_name} zone: {str(e)}"

def check_light_blue_zone(lat: float, lon: float) -> str:
    return check_zone_generic(lat, lon, image_paths["light_blue"], (150, 150, 255), (255, 255, 255), "light blue", "trawling nets")

def check_blue_zone(lat: float, lon: float) -> str:
    return check_zone_generic(lat, lon, image_paths["blue"], (0, 0, 100), (100, 100, 255), "blue", "fire fishing")

def check_green_zone(lat: float, lon: float) -> str:
    return check_zone_generic(lat, lon, image_paths["green"], (0, 100, 0), (100, 255, 100), "green", "trawling nets")

def check_purple_zone(lat: float, lon: float) -> str:
    return check_zone_generic(lat, lon, image_paths["purple"], (100, 0, 100), (255, 100, 255), "purple", "trawling nets")

def check_orange_zone(lat: float, lon: float) -> str:
    return check_zone_generic(lat, lon, image_paths["orange"], (200, 100, 0), (255, 200, 100), "orange", "navigation")

def check_three_zone_map(lat: float, lon: float) -> str:
    if not os.path.exists(image_paths["three_zone"]):
        return "Error checking three-zone map: Warning: Image not found."
    try:
        img = cv2.imread(image_paths["three_zone"])
        if img is None:
            return "Error checking three-zone map: Failed to load image."
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        height, width = img.shape[:2]
        x = int((lon - 7.5) / (12.5 - 7.5) * width)
        y = int((38.5 - lat) / (38.5 - 33.5) * height)
        if not (0 <= x < width and 0 <= y < height):
            return "Error checking three-zone map: Coordinates out of bounds."
        pixel = img_rgb[y, x]
        if np.allclose(pixel, [0, 0, 255], atol=50):
            return "North Zone"
        elif np.allclose(pixel, [0, 255, 0], atol=50):
            return "Center Zone"
        elif np.allclose(pixel, [255, 0, 0], atol=50):
            return "South Zone"
        elif np.allclose(pixel, [255, 255, 255], atol=50):
            return "Land"
        return "Unknown Zone"
    except Exception as e:
        return f"Error checking three-zone map: {str(e)}"

def check_proximity_to_protected_areas(lat: float, lon: float) -> List[Dict]:
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Earth's radius in km
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        return R * c

    protected_areas = [
        {"name": "Archipel de la Galite", "status": "ASPIM (2001)", "lat": 37.5, "lon": 8.9},
        {"name": "Bahiret El Bibane", "status": "Site Ramsar (2007)", "lat": 33.5, "lon": 11.0},
        {"name": "Complexe Lac de Tunis", "status": "Site Ramsar (2013)", "lat": 36.8, "lon": 10.2},
        {"name": "Djerba Bin El Ouedian", "status": "Site Ramsar (2007)", "lat": 33.8, "lon": 10.9},
        {"name": "Iles Kerkennah", "status": "Site Ramsar (2012)", "lat": 34.7, "lon": 11.0},
        {"name": "Iles Kneiss", "status": "Réserve Naturelle (1993), ASPIM (2001)", "lat": 34.4, "lon": 10.3},
        {"name": "Iles Zembra et Zembretta", "status": "Réserve de Biosphère (1977)", "lat": 37.1, "lon": 10.8},
        {"name": "Iles Kuriat", "status": "Proposed AMCP", "lat": 35.8, "lon": 10.9}
    ]
    results = []
    for area in protected_areas:
        distance = haversine(lat, lon, area["lat"], area["lon"])
        proximity = "near" if distance <= 10 else "far" if distance >= 50 else "moderate"
        results.append({"name": area["name"], "distance_km": round(distance, 2), "proximity": proximity})
    return results

def create_zone_map(lat: float, lon: float, results: dict) -> str:
    """Create an interactive map with zone check results"""
    m = folium.Map(location=[lat, lon], zoom_start=8)
    
    # Add marker for current position
    folium.Marker(
        [lat, lon],
        popup="Current Position",
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)
    
    # Define protected areas (same as in check_proximity_to_protected_areas function)
    protected_areas = [
    {"name": "Archipel de la Galite", "status": "ASPIM (2001)", "lat": 37.5, "lon": 8.9},
    {"name": "Bahiret El Bibane", "status": "Site Ramsar (2007)", "lat": 33.5, "lon": 11.0},
    {"name": "Complexe des Zones Humides de Sebkhret Oum Ez-Zessar et Sebkhret El Grine", "status": "Site Ramsar (2013)", "lat": 33.7, "lon": 10.8},
    {"name": "Complexe des Zones Humides des Chott El Guetayate et Sebkhret Dhreia et Oueds Akarit, Rekhama et Meleh", "status": "Site Ramsar (2012)", "lat": 34.0, "lon": 10.0},
    {"name": "Complexe Lac de Tunis", "status": "Site Ramsar (2013)", "lat": 36.8, "lon": 10.2},
    {"name": "Djerba Bin El Ouedian", "status": "Site Ramsar (2007)", "lat": 33.8, "lon": 10.9},
    {"name": "Djerba Guellala", "status": "Site Ramsar (2007)", "lat": 33.7, "lon": 10.9},
    {"name": "Djerba Ras Rmel", "status": "Site Ramsar (2007)", "lat": 33.9, "lon": 10.9},
    {"name": "Galiton", "status": "Réserve naturelle (1980)", "lat": 37.4, "lon": 8.8},
    {"name": "Lague de Boughrara", "status": "Site Ramsar (2012)", "lat": 33.6, "lon": 10.7},
    {"name": "Iles Kerkennah", "status": "Site Ramsar (2012)", "lat": 34.7, "lon": 11.0},
    {"name": "Iles Kneiss", "status": "Réserve Naturelle (1993), ASPIM (2001), Site Ramsar (2007)", "lat": 34.4, "lon": 10.3},
    {"name": "Iles Zembra et Zembretta", "status": "Réserve de Biosphère (1977), Parc National (1973), ASPIM (2003)", "lat": 37.1, "lon": 10.8},
    {"name": "Lague de Ghar El Melh et Delta de la Mejerda", "status": "Site Ramsar (2007)", "lat": 37.2, "lon": 10.2},
    {"name": "Lagunes du Cap Bon Oriental", "status": "Site Ramsar (2007)", "lat": 36.9, "lon": 10.9},
    {"name": "Salines De Thyna", "status": "Site Ramsar (2007)", "lat": 34.2, "lon": 10.1},
    {"name": "Sebkhret Soliman", "status": "Site Ramsar (2007)", "lat": 36.7, "lon": 10.5},
    {"name": "Sebkhret Halk El Manzel Oued Essed", "status": "Site Ramsar (2012)", "lat": 36.6, "lon": 10.6},
    {"name": "Iles Kneiss", "status": "Proposed AMCP", "lat": 34.4, "lon": 10.3},
    {"name": "Archipel de la Galite", "status": "Proposed AMCP", "lat": 37.5, "lon": 8.9},
    {"name": "Iles Kuriat", "status": "Proposed AMCP", "lat": 35.8, "lon": 10.9},
    {"name": "Zembra et Zembretta", "status": "Proposed AMCP", "lat": 37.1, "lon": 10.8},
]
    
    # Add markers for nearby protected areas
    for area in results["protected_areas"]:
        if area["proximity"] in ["near", "moderate"]:
            for pa in protected_areas:
                if pa["name"] == area["name"]:
                    folium.Marker(
                        [pa["lat"], pa["lon"]],
                        popup=f"{pa['name']}: {area['distance_km']}km ({pa['status']})",
                        icon=folium.Icon(
                            color="orange" if area["proximity"] == "near" else "blue",
                            icon="info-sign"
                        )
                    ).add_to(m)
                    break
    
    return m._repr_html_()

def generate_summary(results: dict, lat: float, lon: float) -> str:
    """Generate a human-readable summary of zone check results"""
    summary = []
    compliant = True
    
    # Check basic compliance
    for zone, result in results.items():
        if zone != "protected_areas" and zone != "three_zone":
            if "❌" in result:
                compliant = False
                summary.append(result)
    
    # Format the summary
    summary_text = f"Location: {lat:.6f}, {lon:.6f}\n"
    summary_text += f"Fishing Zone: {results['three_zone']}\n\n"
    
    if compliant:
        summary_text += "✅ Overall Status: COMPLIANT\n"
    else:
        summary_text += "❌ Overall Status: NON-COMPLIANT\n"
        summary_text += "Restrictions:\n" + "\n".join(summary)
    
    # Add protected area warnings
    near_areas = [area for area in results["protected_areas"] if area["proximity"] == "near"]
    if near_areas:
        summary_text += "\n⚠️ Warning: Near protected areas:\n"
        for area in near_areas:
            summary_text += f"- {area['name']} ({area['distance_km']} km)\n"
    
    return summary_text

# Routes
@router.get("/zone-checker", response_class=HTMLResponse)
async def zone_checker_page(request: Request):
    """Zone checker page"""
    return templates.TemplateResponse("zone_checker.html", {"request": request})

@router.get("/check-zones", response_class=HTMLResponse)
async def check_zones_page(
    request: Request,
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """Check zones with interactive map and summary"""
    results = {
        "light_blue_zone": check_light_blue_zone(lat, lon),
        "blue_zone": check_blue_zone(lat, lon),
        "green_zone": check_green_zone(lat, lon),
        "purple_zone": check_purple_zone(lat, lon),
        "orange_zone": check_orange_zone(lat, lon),
        "three_zone": check_three_zone_map(lat, lon),
        "protected_areas": check_proximity_to_protected_areas(lat, lon)
    }
    
    # Generate map and summary
    map_html = create_zone_map(lat, lon, results)
    summary = generate_summary(results, lat, lon)
    
    return templates.TemplateResponse(
        "zone_checker_result.html",
        {
            "request": request,
            "results": results,
            "map": map_html,
            "summary": summary,
            "lat": lat,
            "lon": lon
        }
    )

@router.get("/api/check-zones")
async def check_zones_api(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """API endpoint for zone checking"""
    results = {
        "light_blue_zone": check_light_blue_zone(lat, lon),
        "blue_zone": check_blue_zone(lat, lon),
        "green_zone": check_green_zone(lat, lon),
        "purple_zone": check_purple_zone(lat, lon),
        "orange_zone": check_orange_zone(lat, lon),
        "three_zone": check_three_zone_map(lat, lon),
        "protected_areas": check_proximity_to_protected_areas(lat, lon)
    }
    
    return JSONResponse(content={
        "status": "success",
        "data": results,
        "summary": generate_summary(results, lat, lon)
    })

# Add LLM-based natural language query route
@router.get("/zone-checker/query", response_class=HTMLResponse)
async def zone_checker_query_page(request: Request):
    """Zone checker with natural language query"""
    return templates.TemplateResponse("zone_checker_query.html", {"request": request})

@router.post("/zone-checker/query", response_class=HTMLResponse)
async def process_zone_query(request: Request):
    """Process natural language query for zone checking"""
    form_data = await request.form()
    query = form_data.get("query", "")

    if not query:
        return templates.TemplateResponse(
            "zone_checker_query.html",
            {"request": request, "error": "Please enter a query."}
        )

    try:
        # Use LLM to interpret the query
        response = model.generate_content(query)
        llm_response = response.text

        return templates.TemplateResponse(
            "zone_checker_query.html",
            {"request": request, "query": query, "response": llm_response}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "zone_checker_query.html",
            {"request": request, "error": f"Error processing query: {str(e)}"}
        )

# Add route for Gemini-enhanced zone checking with voice output
@router.post("/zone-checker/gemini")
async def gemini_zone_checker(request: Request):
    """Zone checker with enhanced NLP and voice output"""
    form_data = await request.form()
    lat = form_data.get("latitude")
    lon = form_data.get("longitude")
    query = form_data.get("query", "")

    if not lat or not lon:
        return templates.TemplateResponse(
            "zone_checker_gemini.html",
            {"request": request, "error": "Please provide both latitude and longitude."}
        )

    try:
        lat, lon = float(lat), float(lon)

        # Extract additional context from natural language query if provided
        context = {}
        if query:
            # Classify query intent
            candidate_labels = ["fishing", "navigation", "protected_area", "depth", "general"]
            result = text_classifier(query, candidate_labels)
            context["intent"] = result["labels"][0]
            
            # Extract named entities
            entities = ner_model(query)
            context["entities"] = entities

        # Perform zone checks with context
        results = {
            "light_blue_zone": check_light_blue_zone(lat, lon),
            "blue_zone": check_blue_zone(lat, lon),
            "green_zone": check_green_zone(lat, lon),
            "purple_zone": check_purple_zone(lat, lon),
            "orange_zone": check_orange_zone(lat, lon),
            "three_zone": check_three_zone_map(lat, lon),
            "protected_areas": check_proximity_to_protected_areas(lat, lon)
        }

        # Generate enhanced summary with context
        summary = generate_summary(results, lat, lon)
        if context.get("intent") == "fishing":
            fishing_zones = [k for k, v in results.items() if "✅" in v and "zone" in k]
            if fishing_zones:
                summary += "\n\nFishing is currently allowed in these zones:\n"
                summary += "\n".join([f"- {zone.replace('_', ' ').title()}" for zone in fishing_zones])

        # Create map visualization
        map_html = create_zone_map(lat, lon, results)

        # Convert summary to speech
        audio_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "audio")
        os.makedirs(audio_dir, exist_ok=True)
        audio_path = os.path.join(audio_dir, "zone_summary.mp3")
        
        # Generate speech
        tts_engine.save_to_file(summary, audio_path)
        tts_engine.runAndWait()

        return templates.TemplateResponse(
            "zone_checker_gemini.html",
            {
                "request": request,
                "results": results,
                "summary": summary,
                "map": map_html,
                "audio_file": "/static/audio/zone_summary.mp3",
                "lat": lat,
                "lon": lon,
                "context": context
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "zone_checker_gemini.html",
            {"request": request, "error": f"Error processing request: {str(e)}"}
        )

@router.get("/api/weather")
async def get_weather(lat: float, lon: float):
    """Get weather data for a specific location"""
    try:
        # Using StormGlass API for weather data
        url = "https://api.stormglass.io/v2/weather/point"
        params = {
            "lat": lat,
            "lng": lon,
            "params": ",".join([
                "airTemperature",
                "windSpeed",
                "waterTemperature",
                "windDirection"
            ])
        }
        headers = {
            "Authorization": STORMGLASS_API_KEY
        }
        
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "hours" in data and len(data["hours"]) > 0:
                latest = data["hours"][0]
                return {
                    "status": "success",
                    "forecast": {
                        "temperature": latest.get("airTemperature", {}).get("noaa"),
                        "windSpeed": latest.get("windSpeed", {}).get("noaa"),
                        "waterTemp": latest.get("waterTemperature", {}).get("noaa"),
                        "windDirection": latest.get("windDirection", {}).get("noaa")
                    }
                }
        
        raise HTTPException(
            status_code=response.status_code,
            detail="Error fetching weather data"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )
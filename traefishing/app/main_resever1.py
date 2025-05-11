from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import folium
import os
import sys
import cv2
import numpy as np

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import tools integration
from app.tools_integration import (
    get_current_location,
    get_depth_at_location,
    create_route_map,
    get_ports_map,
    TUNISIAN_PORTS
)

# Import chatbot agent
try:
    from app.chatbot_agent import TraeFishingAgent
    # Initialize the chatbot agent
    chatbot_agent = TraeFishingAgent()
except SyntaxError as e:
    print(f"Error loading chatbot agent: {e}")
    # Define a simple fallback chatbot agent
    class FallbackTraeFishingAgent:
        def __init__(self):
            print("Using fallback chatbot agent due to syntax error in the main agent")
        
        def handle_message(self, message, use_voice=False):
            return {
                "text": "I'm sorry, the chatbot is currently unavailable due to a technical issue. Please try again later.",
                "intent": "error"
            }
        
        def listen(self):
            return "Chatbot listening functionality is unavailable"
    
    chatbot_agent = FallbackTraeFishingAgent()

# Try to import check_proximity_to_protected_areas from the correct location
try:
    from app.tools_integration import check_proximity_to_protected_areas
except ImportError:
    # Fallback: try to import directly from tools
    try:
        from tools.aireProtege import check_proximity_to_protected_areas
    except ImportError:
        # Define a simple version if not available
        def check_proximity_to_protected_areas(lat, lon, distance_threshold=10.0):
            return []

app = FastAPI(title="Tunisian Fisherman Dashboard")

# Mount static files - fix the directory path to use absolute path
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates - Fix the path to use absolute path
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Import and include zone checker routes
from app.routes.zone_checker import router as zone_checker_router
app.include_router(zone_checker_router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/map", response_class=HTMLResponse)
async def show_map(request: Request, governorate: str = None):
    """Show map of ports, optionally filtered by governorate"""
    m = get_ports_map(governorate)
    map_html = m._repr_html_()
    
    return templates.TemplateResponse(
        "map.html", 
        {
            "request": request, 
            "map": map_html,
            "governorate": governorate or "All Tunisia"
        }
    )

@app.get("/current-location", response_class=HTMLResponse)
async def current_location(request: Request):
    """Show current location with detailed information"""
    # Get current location with enhanced information
    location = get_current_location()
    
    # Create a map centered on the current location
    m = folium.Map(location=[location["lat"], location["lon"]], zoom_start=12)
    
    # Add a marker for the current location
    folium.Marker(
        [location["lat"], location["lon"]],
        popup="Current Location",
        icon=folium.Icon(color="red", icon="ship")
    ).add_to(m)
    
    # Add a circle to represent the radar
    folium.Circle(
        radius=5000,  # 5km radius
        location=[location["lat"], location["lon"]],
        color="green",
        fill=True,
        fill_opacity=0.2
    ).add_to(m)
    
    # Add markers for protected areas if any
    for area in location.get("protected_areas", []):
        area_lat, area_lon = area["coordinates"]
        folium.Marker(
            [area_lat, area_lon],
            popup=f"{area['name']} ({area['status']})",
            icon=folium.Icon(color="orange", icon="info-sign")
        ).add_to(m)
    
    # Convert map to HTML
    map_html = m._repr_html_()
    
    # Get depth at current location
    depth_info = get_depth_at_location(location["lat"], location["lon"])
    
    return templates.TemplateResponse(
        "location.html", 
        {
            "request": request, 
            "map": map_html,
            "location": location,
            "depth": depth_info.get("depth", "Unknown")
        }
    )

@app.get("/ports/{governorate}", response_class=HTMLResponse)
async def list_ports(request: Request, governorate: str):
    """List ports for a specific governorate"""
    # Get ports for the governorate
    ports = [port for port in TUNISIAN_PORTS if port["governorate"].lower() == governorate.lower()]
    
    # Create a map with the ports
    m = get_ports_map(governorate)
    map_html = m._repr_html_()
    
    return templates.TemplateResponse(
        "ports.html", 
        {
            "request": request, 
            "ports": ports, 
            "governorate": governorate,
            "map": map_html
        }
    )

@app.get("/route-planner", response_class=HTMLResponse)
async def route_planner(request: Request):
    """Route planner form"""
    return templates.TemplateResponse("route_planner.html", {"request": request})

@app.post("/calculate-route", response_class=HTMLResponse)
async def calculate_route(
    request: Request,
    start_lat: float = Form(...),
    start_lon: float = Form(...),
    end_lat: float = Form(...),
    end_lon: float = Form(...)
):
    """Calculate and display a maritime route"""
    try:
        # Create route map
        m, distance, waypoints = create_route_map(start_lat, start_lon, end_lat, end_lon)
        
        # Convert map to HTML
        map_html = m._repr_html_()
        
        return templates.TemplateResponse(
            "route_result.html", 
            {
                "request": request, 
                "map": map_html,
                "distance": distance,
                "waypoints": waypoints,
                "start_lat": start_lat,
                "start_lon": start_lon,
                "end_lat": end_lat,
                "end_lon": end_lon
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error calculating route: {str(e)}")

@app.get("/depth", response_class=HTMLResponse)
async def depth_calculator(request: Request):
    """Depth calculator form"""
    return templates.TemplateResponse("depth_calculator.html", {"request": request})

@app.post("/calculate-depth", response_class=HTMLResponse)
async def calculate_depth_endpoint(
    request: Request,
    lat: float = Form(...),
    lon: float = Form(...)
):
    """Calculate and display depth at a location"""
    depth_info = get_depth_at_location(lat, lon)
    
    # Check for protected areas
    protected_areas = []
    if depth_info["status"] == "success":
        protected_areas = check_proximity_to_protected_areas(lat, lon)
    
    return templates.TemplateResponse(
        "depth_result.html", 
        {
            "request": request, 
            "depth_info": depth_info,
            "protected_areas": protected_areas
        }
    )

@app.get("/protected-areas", response_class=HTMLResponse)
async def protected_areas(request: Request, lat: float = None, lon: float = None):
    """Show protected areas, optionally near a specific location"""
    if lat is None or lon is None:
        # Get current location if not specified
        location = get_current_location()
        lat, lon = location["lat"], location["lon"]
    
    # Get protected areas
    areas = check_proximity_to_protected_areas(lat, lon, distance_threshold=50.0)
    
    # Create map
    m = folium.Map(location=[lat, lon], zoom_start=8)
    
    # Add marker for reference point
    folium.Marker(
        [lat, lon],
        popup="Reference Point",
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)
    
    # Add markers for protected areas
    for area in areas:
        area_lat, area_lon = area["coordinates"]
        folium.Marker(
            [area_lat, area_lon],
            popup=f"{area['name']} ({area['status']})",
            icon=folium.Icon(
                color="green" if area["proximity"] == "inside" else "orange", 
                icon="leaf"
            )
        ).add_to(m)
        
        # Add circle to show area (approximate)
        folium.Circle(
            radius=5000,  # 5km radius (approximate)
            location=[area_lat, area_lon],
            popup=area["name"],
            color="green" if area["proximity"] == "inside" else "orange",
            fill=True,
            fill_opacity=0.2
        ).add_to(m)
    
    # Convert map to HTML
    map_html = m._repr_html_()
    
    return templates.TemplateResponse(
        "protected_areas.html", 
        {
            "request": request, 
            "map": map_html,
            "areas": areas,
            "lat": lat,
            "lon": lon
        }
    )

@app.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page(request: Request):
    """Render the chatbot interface page"""
    return templates.TemplateResponse("chatbot.html", {"request": request})

@app.post("/api/chatbot")
async def chatbot_api(request: Request):
    """API endpoint for the chatbot"""
    data = await request.json()
    message = data.get('message', '')
    use_voice = data.get('voice', False)
    
    if not message:
        return {"error": "No message provided"}
    
    response = chatbot_agent.handle_message(message, use_voice)
    return response

@app.get("/api/chatbot/listen")
async def chatbot_listen():
    """API endpoint for voice input"""
    try:
        text = chatbot_agent.listen()
        return {"text": text}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
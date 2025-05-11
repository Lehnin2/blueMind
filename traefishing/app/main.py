from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from auth.supabase_client import SupabaseClient
from config.cors_config import setup_cors
import folium
import os
import sys
import cv2
import numpy as np

# Initialiser le client Supabase et le système de sécurité
supabase = SupabaseClient()
security = HTTPBearer()

# Middleware d'authentification
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user = supabase.get_user(token)
    if "error" in user:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Import UI chatbot routes
from routes.ui_chatbot_routes import router as ui_chatbot_router
# Import auth routes
from auth.routes import router as auth_router

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import tools integration
from tools_integration import (
    get_current_location,
    get_depth_at_location,
    create_route_map,
    get_ports_map,
    TUNISIAN_PORTS
)

# Import astronomy and weather tools
from tools.astronomy_weather import (
    get_local_time,
    get_stormglass_astronomy,
    get_weather_data,
    get_location
)

# Import chatbot agent
try:
    from chatbot_agent import TraeFishingAgent
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
    from tools_integration import check_proximity_to_protected_areas
except ImportError:
    # Fallback: try to import directly from tools
    try:
        from tools.aireProtege import check_proximity_to_protected_areas
    except ImportError:
        # Define a simple version if not available
        def check_proximity_to_protected_areas(lat, lon, distance_threshold=10.0):
            return []

app = FastAPI(title="Tunisian Fisherman Dashboard")

# Configure CORS
setup_cors(app)

# Import notifications routes
from routes.notifications_routes import router as notifications_router

# Include notifications router
# Notifications router already included above

# Mount static files with correct configuration
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates - Fix the path to use absolute path
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# QR code generation function
def generate_qr_code(data):
    """Generate QR code for the given data"""
    try:
        import qrcode
        from PIL import Image
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        return img
    except ImportError:
        print("\nQR code generation requires 'qrcode' package. Please install it with 'pip install qrcode[pil]'")
        return None

# Include routers
app.include_router(ui_chatbot_router)
app.include_router(auth_router)
# Notifications router already included above

# Configure CORS
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API endpoint for astronomy and weather data
@app.get("/api/astro-weather")
async def get_astro_weather_data(request: Request):
    """API endpoint to get astronomy and weather data based on client location."""
    # Get location from query parameters
    try:
        lat = float(request.query_params.get('lat', 0))
        lon = float(request.query_params.get('lon', 0))
        
        # Get weather and astronomy data
        weather_data = get_weather_data(lat, lon)
        astronomy_data = get_stormglass_astronomy(lat, lon)
        
        # Simulate navigation data (replace with real data source if available)
        navigation_data = {
            'speed': round(12.5, 1),  # Example speed in km/h
            'depth': round(25.3, 1),  # Example depth in meters
            'wind': round(15.7, 1),   # Example wind speed in km/h
            'heading': round(245.0, 1) # Example heading in degrees
        }
        
        # Prepare response data
        response_data = {
            'navigation': navigation_data,
            'weather': {
                'temperature': weather_data.get('temperature', 25),
                'humidity': weather_data.get('humidity', 60),
                'windSpeed': weather_data.get('windSpeed', 10),
                'condition': weather_data.get('condition', 'clear')
            },
            'astronomy': {
                'sunrise': astronomy_data.get('sunrise', '--:--'),
                'sunset': astronomy_data.get('sunset', '--:--'),
                'moonrise': astronomy_data.get('moonrise', '--:--'),
                'moonset': astronomy_data.get('moonset', '--:--'),
                'moonPhase': astronomy_data.get('moon_phase', '--')
            },
            'timestamp': request.query_params.get('_', '0')  # Include timestamp from request to prevent caching
        }
        
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching astronomy and weather data: {str(e)}")

# Import and include zone checker routes
from routes.zone_checker import router as zone_checker_router
app.include_router(zone_checker_router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Affichage direct du tableau de bord"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page (non-protected)"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/client-data")
async def client_data(lat: float, lon: float):
    """API endpoint to get client data based on location
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        
    Returns:
        dict: Client data including time, weather, and astronomy information
    """
    try:
        # Get local time data
        time_data = get_local_time(lat, lon)
        
        # Get weather data
        weather_data = get_weather_data(lat, lon)
        
        # Get astronomy data
        astronomy_data = get_stormglass_astronomy(lat, lon)
        
        # Combine all data
        return {
            "location": {
                "latitude": lat,
                "longitude": lon
            },
            "time": time_data,
            "weather": weather_data,
            "astronomy": astronomy_data,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

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
    """Calculate and display a maritime route using the advanced A* algorithm"""
    try:
        # Utiliser le planificateur de route maritime avancé
        from tools.maritime_route_planner import MaritimeRoutePlanner
        
        # Créer une instance du planificateur
        planner = MaritimeRoutePlanner()
        
        # Trouver la route optimale
        route = planner.find_route(start_lat, start_lon, end_lat, end_lon)
        
        # Créer la carte avec la route
        m = planner.create_route_map(route, start_lat, start_lon, end_lat, end_lon)
        
        # Calculer la distance totale
        distance = 0
        for i in range(len(route) - 1):
            p1 = route[i]
            p2 = route[i + 1]
            distance += planner._heuristic(p1['lat'], p1['lon'], p2['lat'], p2['lon'])
        
        # Convertir la distance en kilomètres
        distance = round(distance, 2)
        
        # Préparer les waypoints pour l'affichage
        waypoints = [{'lat': point['lat'], 'lon': point['lon'], 'name': f'Point {i}'} 
                     for i, point in enumerate(route)]
        
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
    """Show protected areas, optionally near a specific location (protected)"""
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
    import socket
    import qrcode
    from PIL import Image
    
    # Get local IP address
    def get_local_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP
    
    local_ip = get_local_ip()
    
    print("\n=== TraeFishing Application ===\n")
    print("Choisissez le mode d'exécution:")
    print("1. Localhost uniquement (127.0.0.1)")
    print("2. Téléphone uniquement (" + local_ip + ")")
    print("3. Les deux (localhost et téléphone)\n")
    
    choice = input("Votre choix (1-3): ")
    
    host = "127.0.0.1"
    port = 8002
    
    if choice == "1":
        # Localhost uniquement
        host = "127.0.0.1"
        print(f"\nApplication démarrée sur http://{host}:{port}")
    elif choice == "2":
        # Téléphone uniquement
        host = local_ip
        url = f"http://{host}:{port}"
        print(f"\nApplication démarrée sur {url}")
        
        # Générer et afficher le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Afficher le QR code dans le terminal
        qr.print_ascii()
        print(f"\nScannez le QR code ci-dessus pour accéder à l'application sur votre téléphone")
        print(f"URL: {url}")
    elif choice == "3":
        # Les deux
        host = "0.0.0.0"  # Écoute sur toutes les interfaces
        url = f"http://{local_ip}:{port}"
        print(f"\nApplication démarrée sur:")
        print(f"- Localhost: http://127.0.0.1:{port}")
        print(f"- Réseau: {url}")
        
        # Générer et afficher le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Afficher le QR code dans le terminal
        qr.print_ascii()
        print(f"\nScannez le QR code ci-dessus pour accéder à l'application sur votre téléphone")
        print(f"URL: {url}")
    else:
        print("Choix invalide. Utilisation du mode localhost par défaut.")
    
    uvicorn.run(app, host=host, port=port)
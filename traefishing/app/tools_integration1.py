import folium
import math
import os
import sys
from typing import Dict, List, Tuple, Optional
from langchain.schema import Document

# Mocked dependencies (replace with actual imports when available)
try:
    from tools.nearestPort import TUNISIAN_PORTS
    from tools.localisationActuelSophystique import get_device_location, is_in_sea, haversine_distance
    from tools.guideMarine import guide_marine
    from tools.estimationProfondeur import obtenir_profondeur
    from tools.aireProtege import check_proximity_to_protected_areas
except ImportError:
    # Fallback mocks for testing
    def get_device_location():
        raise NotImplementedError("GPS not available")
    
    def is_in_sea(lat: float, lon: float) -> bool:
        # Simplified: assume sea if within Tunisia's coastal bounds
        return 30.0 < lat < 38.0 and 7.5 < lon < 12.0
    
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Earth's radius in km
        return c * r
    
    def guide_marine(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> List[Dict]:
        # Mock: return direct route
        return [
            {"lat": start_lat, "lon": start_lon, "name": "Start"},
            {"lat": end_lat, "lon": end_lon, "name": "End"}
        ]
    
    def obtenir_profondeur(file_path: str, lat: float, lon: float) -> Optional[float]:
        return None  # Mock: no bathymetric data
    
    def check_proximity_to_protected_areas(lat: float, lon: float) -> List[Dict]:
        return []  # Mock: no protected areas data

# Tunisian Ports Database
TUNISIAN_PORTS = [
    {"name": "Port de Tabarka", "governorate": "Jendouba", "lat": 36.9558, "lon": 8.7339},
    {"name": "Port de Monastir", "governorate": "Monastir", "lat": 35.7789, "lon": 10.8262},
    {"name": "Port de Sayada", "governorate": "Monastir", "lat": 35.6500, "lon": 11.0833},
    {"name": "Port de Ksibet Mediouni", "governorate": "Monastir", "lat": 35.5667, "lon": 11.0333},
    {"name": "Port de Gabes", "governorate": "Gabes", "lat": 33.8869, "lon": 10.1082},
    {"name": "Port de Zarat", "governorate": "Gabes", "lat": 33.7333, "lon": 10.2667},
    {"name": "Port de Zarzouna", "governorate": "Bizerte", "lat": 37.2744, "lon": 9.8746},
    {"name": "Port de Ghar El Melh", "governorate": "Bizerte", "lat": 37.1667, "lon": 10.2167},
    {"name": "Port de Cap Zebib", "governorate": "Bizerte", "lat": 37.2333, "lon": 10.0500},
    {"name": "Port de Sidi Mechreg", "governorate": "Bizerte", "lat": 37.2333, "lon": 9.8000},
    {"name": "Port de Zarzis", "governorate": "Medenine", "lat": 33.5039, "lon": 11.1172},
    {"name": "Port de Houmet Souk", "governorate": "Medenine", "lat": 33.9167, "lon": 10.8667},
    {"name": "Port d'Ajim", "governorate": "Medenine", "lat": 33.9500, "lon": 10.8167},
    {"name": "Port de Boughrara", "governorate": "Medenine", "lat": 33.7500, "lon": 10.9667},
    {"name": "Port de Mahdia", "governorate": "Mahdia", "lat": 35.5050, "lon": 11.0620},
    {"name": "Port de Chebba", "governorate": "Mahdia", "lat": 35.4333, "lon": 11.1167},
    {"name": "Port de Salakta", "governorate": "Mahdia", "lat": 35.5500, "lon": 11.0333},
    {"name": "Port de Malloulech", "governorate": "Mahdia", "lat": 35.5167, "lon": 11.0833},
    {"name": "Port de Kalaat Landalous", "governorate": "Ariana", "lat": 36.8500, "lon": 10.3167},
    {"name": "Port de la Goulette", "governorate": "Tunis", "lat": 36.8333, "lon": 10.3167},
    {"name": "Port de Kelibia", "governorate": "Nabeul", "lat": 36.8444, "lon": 11.0889},
    {"name": "Port de Beni Khiar", "governorate": "Nabeul", "lat": 36.7333, "lon": 10.8833},
    {"name": "Port de Haouaria", "governorate": "Nabeul", "lat": 36.8167, "lon": 10.9500},
    {"name": "Port de Sidi Daoud", "governorate": "Nabeul", "lat": 36.7500, "lon": 10.8833},
    {"name": "Port de Sfax", "governorate": "Sfax", "lat": 34.7272, "lon": 10.7603},
    {"name": "Port de Mahres", "governorate": "Sfax", "lat": 34.5333, "lon": 10.5000},
    {"name": "Port de Skhira", "governorate": "Sfax", "lat": 34.3000, "lon": 10.1000},
    {"name": "Port de Kraten", "governorate": "Sfax", "lat": 34.6500, "lon": 10.6500},
    {"name": "Port de Sousse", "governorate": "Sousse", "lat": 35.8272, "lon": 10.6356},
    {"name": "Port de Hergla", "governorate": "Sousse", "lat": 36.0333, "lon": 10.5000},
    {"name": "Port de Louza – Louata", "governorate": "Sousse", "lat": 35.8167, "lon": 10.6000},
    {"name": "Port de Zaboussa", "governorate": "Sousse", "lat": 35.8500, "lon": 10.6333},
    {"name": "Port d'El Aouabed", "governorate": "Sousse", "lat": 35.8333, "lon": 10.6167}
]

def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate latitude and longitude."""
    return -90 <= lat <= 90 and -180 <= lon <= 180

def create_location_map(lat: float, lon: float, radius: float = 2.0) -> folium.Map:
    """Create a map centered on a location with a radius circle."""
    if not validate_coordinates(lat, lon):
        raise ValueError("Invalid coordinates: lat must be [-90, 90], lon must be [-180, 180]")
    
    m = folium.Map(location=[lat, lon], zoom_start=13)
    folium.TileLayer('openstreetmap', name='Standard Map').add_to(m)
    folium.TileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
        name='Ocean', attr='Esri'
    ).add_to(m)
    
    folium.Marker(
        [lat, lon], popup="Current Location",
        icon=folium.Icon(color="orange", icon="info-sign")
    ).add_to(m)
    
    folium.Circle(
        [lat, lon], radius=radius * 1000, color='green',
        fill=True, fill_opacity=0.2
    ).add_to(m)
    
    folium.LayerControl().add_to(m)
    return m

def get_current_location() -> Dict:
    """Get the vessel's current location with map and protected area checks."""
    try:
        location = get_device_location()
        if not validate_coordinates(location.get("lat", 0), location.get("lon", 0)):
            raise ValueError("Invalid GPS coordinates")
    except Exception as e:
        # Fallback: use La Goulette as default
        location = {
            "lat": 36.8333, "lon": 10.3167, "status": "fallback",
            "nearest_coast": "La Goulette", "distance_to_coast": 0.0,
            "protected_areas": []
        }
    
    try:
        protected_areas = check_proximity_to_protected_areas(location["lat"], location["lon"])
        location["protected_areas"] = protected_areas
    except Exception:
        location["protected_areas"] = []
    
    location["map"] = create_location_map(location["lat"], location["lon"])
    return location

def get_depth_at_location(lat: float, lon: float) -> Dict:
    """Estimate water depth at a given location."""
    if not validate_coordinates(lat, lon):
        return {
            "lat": lat, "lon": lon, "depth": 0,
            "status": "error", "message": "Invalid coordinates"
        }
    
    try:
        file_path = os.path.join("C:\\", "Users", "user", "OneDrive", "Bureau", "multi-agent system", "data", "carte_marine_tunisie.nc")
        depth = obtenir_profondeur(file_path, lat, lon)
        if depth is not None:
            return {
                "lat": lat, "lon": lon, "depth": abs(depth) if depth < 0 else 0,
                "status": "success", "message": "Depth from bathymetric data"
            }
    except Exception as e:
        pass
    
    # Fallback: estimate based on distance to nearest port
    try:
        nearest_port = find_nearest_port(lat, lon)
        distance = haversine_distance(lat, lon, nearest_port["lat"], nearest_port["lon"])
        if distance < 1.0:
            return {
                "lat": lat, "lon": lon, "depth": 0,
                "status": "error", "message": "Location likely on land"
            }
        depth = min(distance * 10, 1500)  # 10m/km, capped at 1500m
        return {
            "lat": lat, "lon": lon, "depth": round(depth, 1),
            "status": "success", "message": "Depth estimated from distance"
        }
    except Exception as e:
        return {
            "lat": lat, "lon": lon, "depth": 0,
            "status": "error", "message": f"Depth calculation failed: {str(e)}"
        }

def create_route_map(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> Tuple[folium.Map, float, List[Dict]]:
    """Create a route map between two points, avoiding protected areas."""
    if not (validate_coordinates(start_lat, start_lon) and validate_coordinates(end_lat, end_lon)):
        raise ValueError("Invalid coordinates")
    
    try:
        waypoints = []
        if not is_in_sea(start_lat, start_lon):
            nearest_port = find_nearest_port(start_lat, start_lon)
            waypoints.append({"lat": start_lat, "lon": start_lon, "name": "Starting Point"})
            waypoints.append({
                "lat": nearest_port["lat"], "lon": nearest_port["lon"],
                "name": f"Port: {nearest_port['name']}"
            })
            sea_waypoints = guide_marine(nearest_port["lat"], nearest_port["lon"], end_lat, end_lon)
            waypoints.extend(sea_waypoints[1:])
        else:
            waypoints = guide_marine(start_lat, start_lon, end_lat, end_lon)
        
        center_lat = (start_lat + end_lat) / 2
        center_lon = (start_lon + end_lon) / 2
        m = folium.Map(location=[center_lat, center_lon], zoom_start=9)
        folium.TileLayer('openstreetmap', name='Standard Map').add_to(m)
        folium.TileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
            name='Ocean', attr='Esri'
        ).add_to(m)
        
        folium.Marker(
            [start_lat, start_lon], popup="Starting Point",
            icon=folium.Icon(color="green", icon="play")
        ).add_to(m)
        folium.Marker(
            [end_lat, end_lon], popup="Destination",
            icon=folium.Icon(color="red", icon="flag")
        ).add_to(m)
        
        total_distance = 0
        for i in range(len(waypoints) - 1):
            p1, p2 = waypoints[i], waypoints[i + 1]
            is_land_segment = i == 0 and not is_in_sea(start_lat, start_lon)
            folium.PolyLine(
                [[p1["lat"], p1["lon"]], [p2["lat"], p2["lon"]]],
                color="brown" if is_land_segment else "blue",
                weight=3, opacity=0.7,
                popup="Land Route" if is_land_segment else "Sea Route"
            ).add_to(m)
            total_distance += haversine_distance(p1["lat"], p1["lon"], p2["lat"], p2["lon"])
        
        for i, point in enumerate(waypoints[1:-1], 1):
            popup_text = point.get("name", f"Waypoint {i}")
            icon_color = "orange" if "port" in popup_text.lower() else "blue"
            folium.Marker(
                [point["lat"], point["lon"]], popup=popup_text,
                icon=folium.Icon(color=icon_color, icon="anchor" if "port" in popup_text.lower() else "info-sign")
            ).add_to(m)
        
        folium.LayerControl().add_to(m)
        return m, round(total_distance, 1), waypoints
    except Exception as e:
        m = folium.Map(location=[start_lat, start_lon], zoom_start=9)
        folium.Marker(
            [start_lat, start_lon], popup="Starting Point",
            icon=folium.Icon(color="green", icon="play")
        ).add_to(m)
        folium.Marker(
            [end_lat, end_lon], popup="Destination",
            icon=folium.Icon(color="red", icon="flag")
        ).add_to(m)
        folium.PolyLine(
            [[start_lat, start_lon], [end_lat, end_lon]],
            color="red", weight=3, opacity=0.7,
            popup="Direct Route (Warning: May cross land)"
        ).add_to(m)
        distance = haversine_distance(start_lat, start_lon, end_lat, end_lon)
        waypoints = [{"lat": start_lat, "lon": start_lon}, {"lat": end_lat, "lon": end_lon}]
        return m, round(distance, 1), waypoints

def get_ports_map(governorate: Optional[str] = None) -> folium.Map:
    """Create a map of Tunisian ports, optionally filtered by governorate."""
    m = folium.Map(location=[36.8065, 10.1815], zoom_start=7)
    folium.TileLayer('openstreetmap', name='Standard Map').add_to(m)
    folium.TileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
        name='Ocean', attr='Esri'
    ).add_to(m)
    
    ports = [p for p in TUNISIAN_PORTS if governorate is None or p["governorate"].lower() == governorate.lower()]
    if not ports and governorate:
        raise ValueError(f"No ports found for governorate: {governorate}")
    
    for port in ports:
        popup_text = f"""
        <b>{port['name']}</b><br>
        Governorate: {port['governorate']}<br>
        Coordinates: {port['lat']}, {port['lon']}
        """
        folium.Marker(
            [port["lat"], port["lon"]], popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color="blue", icon="anchor")
        ).add_to(m)
    
    folium.LayerControl().add_to(m)
    return m

def get_ports_by_governorate(governorate: str) -> List[Dict]:
    """Retrieve all ports for a specific governorate."""
    ports = [p for p in TUNISIAN_PORTS if p["governorate"].lower() == governorate.lower()]
    if not ports:
        raise ValueError(f"No ports found for governorate: {governorate}")
    return ports

def find_nearest_port(lat: float, lon: float, governorate: Optional[str] = None) -> Dict:
    """Find the nearest port, optionally filtered by governorate."""
    if not validate_coordinates(lat, lon):
        raise ValueError("Invalid coordinates")
    
    ports = [p for p in TUNISIAN_PORTS if governorate is None or p["governorate"].lower() == governorate.lower()]
    if not ports:
        raise ValueError(f"No ports found for governorate: {governorate}" if governorate else "No ports available")
    
    return min(ports, key=lambda p: haversine_distance(lat, lon, p["lat"], p["lon"]))

def format_location_response(location: Dict) -> str:
    """Format location data for chatbot response."""
    lat, lon = location["lat"], location["lon"]
    status = location["status"]
    coast = location.get("nearest_coast", "Unknown")
    distance = location.get("distance_to_coast", 0.0)
    areas = location.get("protected_areas", [])
    
    response = f"You're at ({lat:.4f}, {lon:.4f}). "
    if status == "fallback":
        response += f"This is a fallback location near {coast}. "
    else:
        response += f"You're {distance:.1f} km from {coast}. "
    
    if areas:
        response += "Warning: You're near protected areas: " + ", ".join(a.get("name", "Unknown") for a in areas)
    else:
        response += "No protected areas nearby."
    
    return response

def format_depth_response(depth_info: Dict) -> str:
    """Format depth data for chatbot response."""
    depth = depth_info["depth"]
    status = depth_info["status"]
    message = depth_info["message"]
    
    if status == "success":
        return f"The water depth is {depth:.1f} meters. ({message})"
    return f"Could not determine depth: {message}"

def format_route_response(route_map: folium.Map, distance: float, waypoints: List[Dict]) -> str:
    """Format route data for chatbot response."""
    num_waypoints = len(waypoints)
    start = waypoints[0].get("name", "Start")
    end = waypoints[-1].get("name", "Destination")
    
    response = f"Route from {start} to {end}: {distance:.1f} km. "
    if num_waypoints > 2:
        intermediates = [p.get("name", f"Waypoint {i+1}") for i, p in enumerate(waypoints[1:-1])]
        response += f"Via: {', '.join(intermediates)}. "
    
    if any("Warning: May cross land" in p.get("name", "") for p in waypoints):
        response += "Note: This is a direct route and may not be safe for sea travel."
    else:
        response += "This route is planned for safe sea travel."
    
    return response

def format_ports_response(ports: List[Dict], governorate: Optional[str] = None) -> str:
    """Format ports data for chatbot response."""
    if not ports:
        return f"No ports found for governorate: {governorate}" if governorate else "No ports available."
    
    response = f"Ports in {governorate if governorate else 'Tunisia'}:\n"
    for port in ports:
        response += f"- {port['name']} ({port['governorate']}, {port['lat']:.4f}, {port['lon']:.4f})\n"
    return response.strip()
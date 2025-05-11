

"""
Integration module for various fishing tools and data sources.
This module provides functions to interact with maps, location data,
depth calculations, and route planning.
"""

import folium
import random
import math
import os
import sys

# Import tools from the tools directory
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from tools.nearestPort import TUNISIAN_PORTS, find_nearest_port
from tools.mapLocation import get_map_location
from tools.localisationActuelSophystique import get_device_location, is_in_sea, haversine_distance
from tools.liveGuideMarine import live_guide_marine
from tools.guideMarine import guide_marine
from tools.estimationProfondeur import obtenir_profondeur
from tools.aireProtege import check_proximity_to_protected_areas

# Define a function to get the current location
def create_location_map(lat, lon, radius=2.0):
    """
    Create a map centered on the current location with a radius circle.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        radius (float): Radius in kilometers
        
    Returns:
        folium.Map: Map with location marker and radius circle
    """
    # Create a map centered on the location
    m = folium.Map(location=[lat, lon], zoom_start=13)
    
    # Add base map layers for switching between views
    folium.TileLayer('openstreetmap', name='Standard Map').add_to(m)
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 
                    name='Satellite', 
                    attr='Esri').add_to(m)
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}', 
                    name='Ocean', 
                    attr='Esri').add_to(m)
    
    # Add a marker for the exact location
    folium.Marker(
        [lat, lon],
        popup="Current Location",
        icon=folium.Icon(color="orange", icon="info-sign")
    ).add_to(m)
    
    # Add a circle to show the approximate radius
    folium.Circle(
        [lat, lon],
        radius=radius * 1000,  # Convert km to meters
        color='green',
        fill=True,
        fill_opacity=0.2
    ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m

# Update the get_current_location function to include map creation
def get_current_location():
    """
    Get the current location of the vessel.
    In a real application, this would use GPS data.
    For demonstration, we use the get_device_location function.
    
    Returns:
        dict: Location information including coordinates and nearby features
    """
    try:
        # Try to get the actual device location
        location = get_device_location()
    except Exception as e:
        print(f"Error getting device location: {e}")
        # Fallback to a location near La Goulette port
        location = {
            "lat": 36.8183 + random.uniform(-0.05, 0.05),
            "lon": 10.3053 + random.uniform(-0.05, 0.05),
            "status": "at sea",
            "nearest_coast": "La Goulette",
            "distance_to_coast": round(random.uniform(1.0, 5.0), 1),
            "protected_areas": []
        }
    
    # Check if near any protected areas
    protected_areas = check_proximity_to_protected_areas(location["lat"], location["lon"])
    if protected_areas:
        location["protected_areas"] = protected_areas
    
    # Create a map for the location
    location["map"] = create_location_map(location["lat"], location["lon"])
    
    return location

def get_depth_at_location(lat, lon):
    """
    Calculate the estimated depth at a given location.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        
    Returns:
        dict: Depth information
    """
    try:
        # Try to get depth from the bathymetric data
        fichier_nc = os.path.join("C:\\", "Users", "user", "OneDrive", "Bureau", "multi-agent system", "data", "carte_marine_tunisie.nc")
        if os.path.exists(fichier_nc):
            depth = obtenir_profondeur(fichier_nc, lat, lon)
            if depth is not None:
                return {
                    "lat": lat,
                    "lon": lon,
                    "depth": abs(depth) if depth < 0 else 0,
                    "status": "success",
                    "message": "Depth calculated using bathymetric data"
                }
    except Exception as e:
        print(f"Error getting depth from bathymetric data: {e}")
    
    # Fallback to estimation based on distance from shore
    try:
        # Check if on land (simplified check for Tunisia)
        if (lat > 30.0 and lat < 38.0 and lon > 7.5 and lon < 12.0):
            # Calculate distance to nearest coast (simplified)
            min_distance = float('inf')
            for port in TUNISIAN_PORTS:
                distance = haversine_distance(lat, lon, port["lat"], port["lon"])
                min_distance = min(min_distance, distance)
            
            # If very close to a port, likely on land
            if min_distance < 1.0:
                return {
                    "lat": lat,
                    "lon": lon,
                    "depth": 0,
                    "status": "error",
                    "message": "Location appears to be on land"
                }
            
            # Simplified depth model: deeper as you move away from coast
            depth = min_distance * 10  # 10 meters per km from shore, simplified
            
            # Add some randomness to make it more realistic
            depth = depth * random.uniform(0.8, 1.2)
            
            # Cap at reasonable maximum depth for Mediterranean
            depth = min(depth, 1500)
            
            return {
                "lat": lat,
                "lon": lon,
                "depth": round(depth, 1),
                "status": "success",
                "message": "Depth calculated using distance-based estimation"
            }
    except Exception as e:
        print(f"Error estimating depth: {e}")
    
    return {
        "lat": lat,
        "lon": lon,
        "depth": 0,
        "status": "error",
        "message": "Unable to calculate depth"
    }

def create_route_map(start_lat, start_lon, end_lat, end_lon):
    """
    Create a route map between two points using the advanced maritime route planner.
    
    Args:
        start_lat (float): Starting latitude
        start_lon (float): Starting longitude
        end_lat (float): Ending latitude
        end_lon (float): Ending longitude
        
    Returns:
        tuple: (folium.Map, distance, waypoints)
    """
    try:
        # Utiliser le planificateur de route maritime avancé avec A*
        from app.tools.maritime_route_planner import MaritimeRoutePlanner
        
        # Créer une instance du planificateur
        planner = MaritimeRoutePlanner()
        
        # Check if starting point is on land
        if not is_in_sea(start_lat, start_lon):
            print("Starting point appears to be on land. Finding nearest port...")
            # Find the nearest port to the starting point
            nearest_port = find_nearest_port(start_lat, start_lon)
            if nearest_port:
                print(f"Routing through nearest port: {nearest_port['name']}")
                # Create a waypoint at the nearest port
                port_waypoint = {
                    "lat": nearest_port["lat"],
                    "lon": nearest_port["lon"],
                    "name": f"Nearest Port: {nearest_port['name']}"
                }
                
                # First leg: from start to nearest port (land route)
                land_distance = haversine_distance(start_lat, start_lon, nearest_port["lat"], nearest_port["lon"])
                
                # Second leg: from port to destination (sea route) using A* algorithm
                try:
                    sea_route = planner.find_route(nearest_port["lat"], nearest_port["lon"], end_lat, end_lon)
                    # If sea route found, combine the routes
                    waypoints = [{"lat": start_lat, "lon": start_lon, "name": "Starting Point"}]
                    waypoints.append(port_waypoint)
                    
                    # Convert sea_route to waypoints format
                    for i, point in enumerate(sea_route[1:], 1):  # Skip the first point as it's the port
                        waypoints.append({"lat": point["lat"], "lon": point["lon"], "name": f"Sea Point {i}"})
                except Exception as e:
                    print(f"Error finding sea route from port: {e}")
                    # If sea route fails, just go directly from port to destination
                    waypoints = [
                        {"lat": start_lat, "lon": start_lon, "name": "Starting Point"},
                        port_waypoint,
                        {"lat": end_lat, "lon": end_lon, "name": "Destination"}
                    ]
            else:
                print("No nearby port found. Using direct route.")
                # If no port found, use A* algorithm for direct route
                route = planner.find_route(start_lat, start_lon, end_lat, end_lon)
                waypoints = [{"lat": point["lat"], "lon": point["lon"], "name": f"Point {i}"} 
                             for i, point in enumerate(route)]
        else:
            # Starting point is already at sea, use A* algorithm for sea routing
            route = planner.find_route(start_lat, start_lon, end_lat, end_lon)
            waypoints = [{"lat": point["lat"], "lon": point["lon"], "name": f"Point {i}"} 
                         for i, point in enumerate(route)]
        
        # Create a map centered between the start and end points
        center_lat = (start_lat + end_lat) / 2
        center_lon = (start_lon + end_lon) / 2
        m = folium.Map(location=[center_lat, center_lon], zoom_start=9)
        
        # Add base map layers for switching between views
        folium.TileLayer('openstreetmap', name='Standard Map').add_to(m)
        folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 
                        name='Satellite', 
                        attr='Esri').add_to(m)
        folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}', 
                        name='Ocean', 
                        attr='Esri').add_to(m)
        
        # Add markers for start and end
        folium.Marker(
            [start_lat, start_lon],
            popup="Starting Point",
            icon=folium.Icon(color="green", icon="play")
        ).add_to(m)
        
        folium.Marker(
            [end_lat, end_lon],
            popup="Destination",
            icon=folium.Icon(color="red", icon="flag")
        ).add_to(m)
        
        # Create a line for the route
        route_points = [[point["lat"], point["lon"]] for point in waypoints]
        
        # Add different colored segments for land and sea
        for i in range(len(waypoints) - 1):
            point1 = waypoints[i]
            point2 = waypoints[i + 1]
            
            # Determine if this segment is land or sea
            is_land_segment = i == 0 and not is_in_sea(start_lat, start_lon)
            
            folium.PolyLine(
                [[point1["lat"], point1["lon"]], [point2["lat"], point2["lon"]]],
                color="brown" if is_land_segment else "blue",
                weight=3,
                opacity=0.7,
                popup="Land Route" if is_land_segment else "Sea Route"
            ).add_to(m)
        
        # Add markers for each waypoint with improved visibility
        for i, point in enumerate(waypoints[1:-1], 1):  # Skip start and end
            popup_text = point.get("name", f"Waypoint {i}")
            icon_color = "orange" if "port" in popup_text.lower() else "blue"
            
            # Ajouter un numéro au popup pour identifier facilement les waypoints
            detailed_popup = f"""<b>Waypoint {i}</b><br>
            Type: {"Port" if "port" in popup_text.lower() else "Point de navigation A*"}<br>
            Coordonnées: {point["lat"]:.6f}°, {point["lon"]:.6f}°
            """
            
            folium.Marker(
                [point["lat"], point["lon"]],
                popup=folium.Popup(detailed_popup, max_width=200),
                tooltip=f"Point {i}",
                icon=folium.Icon(color=icon_color, icon="anchor" if "port" in popup_text.lower() else "info-sign")
            ).add_to(m)
            
            # Ajouter un petit cercle avec le numéro du waypoint
            folium.CircleMarker(
                location=[point["lat"], point["lon"]],
                radius=12,
                color=icon_color,
                fill=True,
                fill_color=icon_color,
                fill_opacity=0.7,
                popup=f"Point {i}",
                tooltip=f"Point {i}",
                weight=1
            ).add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Calculate total distance
        total_distance = 0
        for i in range(len(waypoints) - 1):
            point1 = waypoints[i]
            point2 = waypoints[i + 1]
            segment_distance = haversine_distance(point1["lat"], point1["lon"], point2["lat"], point2["lon"])
            total_distance += segment_distance
        
        return m, round(total_distance, 1), waypoints
    except Exception as e:
        print(f"Error creating route map: {e}")
        # Create a simple map with just start and end points
        m = folium.Map(location=[start_lat, start_lon], zoom_start=9)
        folium.Marker(
            [start_lat, start_lon],
            popup="Starting Point",
            icon=folium.Icon(color="green", icon="play")
        ).add_to(m)
        folium.Marker(
            [end_lat, end_lon],
            popup="Destination",
            icon=folium.Icon(color="red", icon="flag")
        ).add_to(m)
        
        # Direct line
        folium.PolyLine(
            [[start_lat, start_lon], [end_lat, end_lon]],
            color="red",
            weight=3,
            opacity=0.7,
            popup="Direct Route (Warning: May cross land)"
        ).add_to(m)
        
        # Calculate direct distance
        direct_distance = haversine_distance(start_lat, start_lon, end_lat, end_lon)
        waypoints = [
            {"lat": start_lat, "lon": start_lon},
            {"lat": end_lat, "lon": end_lon}
        ]
        
        return m, round(direct_distance, 1), waypoints

def get_ports_map(governorate=None):
    """
    Create a map of ports, optionally filtered by governorate.
    
    Args:
        governorate (str, optional): Filter ports by governorate. Defaults to None.
        
    Returns:
        folium.Map: Map with port markers
    """
    # Center map on Tunisia
    m = folium.Map(location=[36.8065, 10.1815], zoom_start=7)
    
    # Add base map layers for switching between views
    folium.TileLayer('openstreetmap', name='Standard Map').add_to(m)
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 
                    name='Satellite', 
                    attr='Esri').add_to(m)
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}', 
                    name='Ocean', 
                    attr='Esri').add_to(m)
    
    # Filter ports by governorate if specified
    if governorate:
        ports = [port for port in TUNISIAN_PORTS if port["governorate"].lower() == governorate.lower()]
    else:
        ports = TUNISIAN_PORTS
    
    # Add markers for each port
    for port in ports:
        popup_text = f"""
        <b>{port['name']}</b><br>
        Type: {port.get('type', 'N/A')}<br>
        Facilities: {port.get('facilities', 'N/A')}<br>
        Coordinates: {port['lat']}, {port['lon']}
        """
        
        folium.Marker(
            [port["lat"], port["lon"]],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color="blue", icon="anchor")
        ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m
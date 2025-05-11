# tools/localization_tool.py

import geocoder
import requests
import math
from tools.nearestPort import find_nearest_port

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula (in km)."""
    try:
        lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    except (ValueError, TypeError):
        return float('inf')
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Earth radius in km
    return c * r

def is_in_sea(lat, lon, timeout=5):
    """Check if a point is in the sea using Overpass API."""
    try:
        query = f"""
        [out:json][timeout:{timeout}];
        (
          way["natural"="water"](around:10000,{lat},{lon});
          relation["natural"="water"](around:10000,{lat},{lon});
          node["place"="sea"](around:10000,{lat},{lon});
          way["highway"](around:10000,{lat},{lon});
          way["landuse"](around:10000,{lat},{lon});
        );
        out body;
        """
        url = "http://overpass-api.de/api/interpreter"
        response = requests.post(url, data={"data": query}, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        elements = data.get("elements", [])
        water_count = sum(
            1 for element in elements
            if element.get("tags", {}).get("natural") == "water" or
               element.get("tags", {}).get("place") == "sea"
        )
        land_count = sum(
            1 for element in elements
            if "highway" in element.get("tags", {}) or
               "landuse" in element.get("tags", {})
        )
        print(f"Debug: Overpass for ({lat}, {lon}) - {len(elements)} elements, water_count: {water_count}, land_count: {land_count}")
        return water_count > land_count or (water_count > 0 and land_count == 0)
    except Exception as e:
        print(f"Overpass API error: {e}. Falling back to port proximity.")
        try:
            nearest = find_nearest_port(lat, lon)
            distance = haversine_distance(lat, lon, nearest["lat"], nearest["lon"])
            is_sea = distance > 2.0
            print(f"Debug: Fallback - Distance to {nearest['name']}: {distance:.2f} km, is_sea: {is_sea}")
            return is_sea
        except Exception:
            print("Fallback error. Assuming not sea.")
            return False

def get_device_location():
    """Retrieve the current GPS coordinates and coastal proximity.
    
    Returns:
        dict: {
            'lat': float, 'lon': float,
            'status': str ('at sea' | 'near coast' | 'far from coast'),
            'nearest_coast': str (name of nearest port/coast),
            'distance_to_coast': float (km to nearest coast)
        }
    """
    try:
        # Try IP-based geolocation
        g = geocoder.ip('me')
        if not g.ok:
            raise Exception("IP geolocation failed")
        lat, lon = g.lat, g.lng
    except Exception as e:
        print(f"Error getting location: {e}. Please provide coordinates or use GPS.")
        raise Exception("Geolocation unavailable")

    # Check sea/coast status
    is_sea = is_in_sea(lat, lon)
    try:
        nearest = find_nearest_port(lat, lon)
        nearest_coast = nearest["name"]
        distance_to_coast = haversine_distance(lat, lon, nearest["lat"], nearest["lon"])
    except Exception as e:
        print(f"Error finding nearest coast: {e}. Assuming unknown coast.")
        nearest_coast = "Unknown"
        distance_to_coast = float('inf')

    # Determine status
    if is_sea and distance_to_coast > 5.0:
        status = "at sea"
    elif distance_to_coast <= 5.0:
        status = "near coast"
    else:
        status = "far from coast"

    return {
        "lat": lat,
        "lon": lon,
        "status": status,
        "nearest_coast": nearest_coast,
        "distance_to_coast": distance_to_coast
    }
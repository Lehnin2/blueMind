import math
from typing import List, Dict, Tuple

# List of protected areas with name, status, and approximate coordinates
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

# Haversine formula to calculate distance between two points (in kilometers)
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Radius of the Earth in kilometers
    R = 6371.0
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return distance

# Function to determine proximity to protected areas
def check_proximity_to_protected_areas(user_lat: float, user_lon: float, distance_threshold: float = 10.0, inside_threshold: float = 1.0) -> List[Dict]:
    """
    Check if a location (user_lat, user_lon) is within or near protected areas.
    
    Args:
        user_lat (float): User's latitude.
        user_lon (float): User's longitude.
        distance_threshold (float): Distance in km to consider as "near" (default: 10 km).
        inside_threshold (float): Distance in km to consider as "inside" (default: 1 km).
    
    Returns:
        List[Dict]: List of nearby or containing protected areas with details.
    """
    results = []
    
    for area in protected_areas:
        distance = haversine(user_lat, user_lon, area["lat"], area["lon"])
        if distance <= distance_threshold:
            # Determine if the user is "inside" or "near" the area
            proximity_status = "inside" if distance <= inside_threshold else "near"
            results.append({
                "name": area["name"],
                "status": area["status"],
                "distance_km": round(distance, 2),
                "proximity": proximity_status,
                "coordinates": (area["lat"], area["lon"])
            })
    
    # Sort by distance
    results.sort(key=lambda x: x["distance_km"])
    return results

# Function to format the results
def format_proximity_results(results: List[Dict]) -> str:
    if not results:
        return "Aucune aire protégée ou gérée à proximité de votre position."
    
    response = "Aires protégées ou gérées à proximité de votre position :\n"
    for result in results:
        response += f"- {result['name']} ({result['status']}) : {result['proximity'].capitalize()} ({result['distance_km']} km) à la position ({result['coordinates'][0]}, {result['coordinates'][1]})\n"
    return response

# Example usage
if __name__ == "__main__":
    # Example: User's location near Zembra et Zembretta (37.1, 10.8)
    user_lat = 37.1
    user_lon = 10.8
    
    # Check proximity
    proximity_results = check_proximity_to_protected_areas(user_lat, user_lon)
    
    # Format and print results
    print(format_proximity_results(proximity_results))
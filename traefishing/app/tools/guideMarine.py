# tools/guide_marine_tool.py

import math
import requests
import time

def guide_marine(start_lat, start_lon, dest_lat, dest_lon):
    """Guide a fisherman from a starting point to a destination, ensuring the path stays at sea using OpenStreetMap.
    
    Args:
        start_lat (float): Starting latitude.
        start_lon (float): Starting longitude.
        dest_lat (float): Destination latitude.
        dest_lon (float): Destination longitude.
    
    Returns:
        list: List of waypoints [{'lat': float, 'lon': float}, ...] forming a maritime path.
              Returns [{'lat': start_lat, 'lon': start_lon}] if destination is invalid or unreachable.
    """
    def is_in_sea(lat, lon, timeout=5):
        """Check if a point is in the sea using Overpass API."""
        try:
            # Overpass QL query to check for water (sea) around the point
            query = f"""
            [out:json][timeout:{timeout}];
            (
              way["natural"="water"](around:1000,{lat},{lon});
              relation["natural"="water"](around:1000,{lat},{lon});
            );
            out body;
            """
            url = "http://overpass-api.de/api/interpreter"
            response = requests.post(url, data={"data": query}, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            
            # If water features are found, assume point is in sea
            return len(data.get("elements", [])) > 0
        except Exception as e:
            print(f"Overpass API error: {e}. Falling back to port proximity check.")
            # Fallback: Assume point is on land if near a known port
            from tools.nearestPort import find_nearest_port
            nearest = find_nearest_port(lat, lon)
            distance = haversine_distance(lat, lon, nearest["lat"], nearest["lon"])
            return distance > 1.0  # More than 1 km from port = likely sea

    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula (in km)."""
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Earth radius in km
        return c * r

    def interpolate_points(lat1, lon1, lat2, lon2, num_points=10):
        """Generate intermediate points between start and destination."""
        points = []
        for i in range(num_points + 1):
            fraction = i / num_points
            lat = lat1 + fraction * (lat2 - lat1)
            lon = lon1 + fraction * (lon2 - lon1)
            points.append({"lat": lat, "lon": lon})
        return points

    def adjust_path_around_land(path):
        """Adjust path to avoid land by adding an offshore midpoint."""
        mid_idx = len(path) // 2
        mid_lat = path[mid_idx]["lat"]
        mid_lon = path[mid_idx]["lon"]
        
        # Try shifting midpoint offshore (east or west along Tunisian coast)
        attempts = [
            (mid_lat, mid_lon + 0.5),  # Shift east
            (mid_lat, mid_lon - 0.5),  # Shift west
            (mid_lat + 0.5, mid_lon),  # Shift north
            (mid_lat - 0.5, mid_lon)   # Shift south
        ]
        
        for new_lat, new_lon in attempts:
            if is_in_sea(new_lat, new_lon):
                # Create new path via offshore midpoint
                path1 = interpolate_points(path[0]["lat"], path[0]["lon"], new_lat, new_lon, num_points=5)
                path2 = interpolate_points(new_lat, new_lon, path[-1]["lat"], path[-1]["lon"], num_points=5)
                return path1[:-1] + path2  # Combine, avoid duplicate midpoint
        
        print("Cannot find sea path. Returning start point.")
        return [path[0]]

    # Validate inputs
    try:
        start_lat, start_lon, dest_lat, dest_lon = map(float, [start_lat, start_lon, dest_lat, dest_lon])
    except (ValueError, TypeError):
        print("Invalid coordinates. Returning start point.")
        return [{"lat": start_lat, "lon": start_lon}]

    # Check if start or destination is in sea
    if not is_in_sea(start_lat, start_lon):
        print("Starting point is on land. Choose a point at sea.")
        return [{"lat": start_lat, "lon": start_lon}]
    if not is_in_sea(dest_lat, dest_lon):
        print("Destination is on land. Choose a point at sea.")
        return [{"lat": start_lat, "lon": start_lon}]

    # Generate initial straight-line path
    path = interpolate_points(start_lat, start_lon, dest_lat, dest_lon)

    # Check each waypoint for land
    for point in path[1:-1]:  # Skip start and end (already checked)
        if not is_in_sea(point["lat"], point["lon"]):
            print("Path crosses land. Adjusting to stay at sea.")
            return adjust_path_around_land(path)

    # If all points are in sea, return path
    return path
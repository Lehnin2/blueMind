# tools/live_guide_marine_tool.py

import math
import requests
import time
from tools.localisationActuelSophystique import get_device_location, is_in_sea, haversine_distance
from tools.nearestPort import find_nearest_port

def interpolate_points(lat1, lon1, lat2, lon2, num_points=5):
    """Generate intermediate points between start and destination."""
    try:
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    except (ValueError, TypeError):
        return []
    points = []
    for i in range(num_points + 1):
        fraction = i / num_points
        lat = lat1 + fraction * (lat2 - lat1)
        lon = lon1 + fraction * (lon2 - lon1)
        points.append({"lat": lat, "lon": lon})
    return points

def get_sea_starting_point(lat, lon):
    """If position is on land, return a nearby sea point."""
    if is_in_sea(lat, lon):
        return lat, lon
    print("Current position is on land. Finding nearby sea point...")
    try:
        nearest = find_nearest_port(lat, lon)
        port_lat, port_lon = nearest["lat"], nearest["lon"]
        # Offset 5 km east
        offset_km = 5.0
        earth_radius = 6371.0
        lat_rad = math.radians(port_lat)
        lon_rad = math.radians(port_lon)
        angular_distance = offset_km / earth_radius
        new_lat = math.degrees(lat_rad + angular_distance * math.cos(math.radians(90)))
        new_lon = math.degrees(lon_rad + angular_distance * math.sin(math.radians(90)) / math.cos(lat_rad))
        if is_in_sea(new_lat, new_lon):
            print(f"Using sea point near {nearest['name']}: ({new_lat}, {new_lon})")
            return new_lat, new_lon
        print("Cannot find sea point. Using port.")
        return port_lat, port_lon
    except Exception as e:
        print(f"Error finding sea point: {e}. Using default sea point.")
        return 36.85, 10.35  # Off La Goulette

def simulate_movement(current_lat, current_lon, dest_lat, dest_lon, step_km=10.0):
    """Simulate moving toward destination by step_km."""
    distance = haversine_distance(current_lat, current_lon, dest_lat, dest_lon)
    if distance <= step_km:
        return dest_lat, dest_lon
    fraction = step_km / distance
    new_lat = current_lat + fraction * (dest_lat - current_lat)
    new_lon = current_lon + fraction * (dest_lon - current_lon)
    return new_lat, new_lon

def live_guide_marine(dest_lat, dest_lon, update_interval=10, distance_threshold=0.1, simulate=True):
    """Guide a fisherman to any destination in real-time, keeping path at sea.
    
    Args:
        dest_lat (float): Destination latitude.
        dest_lon (float): Destination longitude.
        update_interval (int): Seconds between position updates.
        distance_threshold (float): Distance (km) to consider 'arrived'.
        simulate (bool): Simulate movement for testing.
    
    Returns:
        list: Final path taken [{'lat': float, 'lon': float}, ...].
    """
    try:
        dest_lat, dest_lon = float(dest_lat), float(dest_lon)
    except (ValueError, TypeError):
        print("Invalid destination coordinates.")
        return []

    print(f"Starting navigation to ({dest_lat}, {dest_lon})...")
    path_history = []
    simulated_pos = None

    while True:
        # Get current position
        try:
            if simulate and simulated_pos:
                current_lat, current_lon = simulated_pos
                current_status = "simulated sea"
                nearest_coast = "N/A"
                distance_to_coast = 0.0
            else:
                pos = get_device_location()
                current_lat, current_lon = pos["lat"], pos["lon"]
                current_status = pos["status"]
                nearest_coast = pos["nearest_coast"]
                distance_to_coast = pos["distance_to_coast"]
                # Adjust if on land
                if current_status == "far from coast":
                    current_lat, current_lon = get_sea_starting_point(current_lat, current_lon)
                    current_status = "simulated sea"
                    nearest_coast = find_nearest_port(current_lat, current_lon)["name"]
                    distance_to_coast = haversine_distance(current_lat, current_lon, pos["lat"], pos["lon"])
                if simulate:
                    simulated_pos = (current_lat, current_lon)
        except Exception as e:
            print(f"Error getting position: {e}. Using default sea point.")
            current_lat, current_lon = 36.85, 10.35
            current_status = "default sea"
            nearest_coast = "La Goulette"
            distance_to_coast = 0.0
            if simulate:
                simulated_pos = (current_lat, current_lon)

        # Check if reached destination
        distance_to_dest = haversine_distance(current_lat, current_lon, dest_lat, dest_lon)
        if distance_to_dest <= distance_threshold:
            print(f"Arrived at destination! Distance: {distance_to_dest:.2f} km")
            path_history.append({"lat": current_lat, "lon": current_lon})
            return path_history

        # Calculate path to destination
        path = interpolate_points(current_lat, current_lon, dest_lat, dest_lon)
        final_path = path
        for point in path[1:-1]:
            if not is_in_sea(point["lat"], point["lon"]):
                print("Path crosses land. Adjusting...")
                mid_lat = (current_lat + dest_lat) / 2
                mid_lon = (current_lon + dest_lon) / 2
                attempts = [
                    (mid_lat, mid_lon + 0.5),
                    (mid_lat, mid_lon - 0.5),
                    (mid_lat + 0.5, mid_lon),
                    (mid_lat - 0.5, mid_lon)
                ]
                new_path = None
                for new_lat, new_lon in attempts:
                    if is_in_sea(new_lat, new_lon):
                        path1 = interpolate_points(current_lat, current_lon, new_lat, new_lon, 2)
                        path2 = interpolate_points(new_lat, new_lon, dest_lat, dest_lon, 2)
                        new_path = path1[:-1] + path2
                        break
                if new_path:
                    final_path = new_path
                    print("Adjusted path:", final_path)
                else:
                    print("Cannot find sea path. Continuing with best effort.")
                break

        # Update path history
        path_history.append({"lat": current_lat, "lon": current_lon})
        print(f"Current position: ({current_lat}, {current_lon})")
        print(f"Status: {current_status}")
        print(f"Nearest coast: {nearest_coast}, Distance: {distance_to_coast:.2f} km")
        print(f"Distance to destination: {distance_to_dest:.2f} km")
        print(f"Next waypoint: {final_path[1] if len(final_path) > 1 else final_path[0]}")
        print("Waiting for next update...")

        # Simulate movement
        if simulate:
            simulated_pos = simulate_movement(current_lat, current_lon, dest_lat, dest_lon)

        # Wait for next update
        time.sleep(update_interval)

    return path_history
import requests
import geocoder
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz


def get_location():
    """
    Get the current location (latitude, longitude) using IP-based geolocation.
    
    Returns:
        tuple: (latitude, longitude) or None if failed.
    """
    try:
        g = geocoder.ip('me')
        if g.latlng:
            return g.latlng  # Returns [lat, lon]
        return None
    except Exception as e:
        print(f"Error getting location: {e}")
        return None


def get_local_time(lat, lon):
    """
    Get the current local time based on latitude and longitude.
    
    Args:
        lat (float): Latitude.
        lon (float): Longitude.
    
    Returns:
        dict: Formatted local time information or error message.
    """
    try:
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat=lat, lng=lon)
        if not timezone_str:
            return {"error": "Could not determine timezone."}
        
        timezone = pytz.timezone(timezone_str)
        local_time = datetime.now(timezone)
        
        # Format date and time components
        return {
            "full_datetime": local_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "time": local_time.strftime("%H:%M:%S"),
            "date": local_time.strftime("%Y-%m-%d"),
            "day_name": local_time.strftime("%A"),  # Full day name (e.g., Monday)
            "day_short": local_time.strftime("%a"),  # Short day name (e.g., Mon)
            "month_name": local_time.strftime("%B"),  # Full month name
            "month_short": local_time.strftime("%b"),  # Short month name
            "year": local_time.strftime("%Y"),
            "hour": local_time.strftime("%H"),
            "minute": local_time.strftime("%M"),
            "second": local_time.strftime("%S"),
            "timezone": local_time.strftime("%Z"),
            "timezone_offset": local_time.strftime("%z")
        }
    except Exception as e:
        return {"error": f"Error getting local time: {e}"}


def get_stormglass_astronomy(lat, lon, api_key=None):
    """
    Fetch astronomical data from Storm Glass API for a given location.
    
    Args:
        lat (float): Latitude.
        lon (float): Longitude.
        api_key (str, optional): Storm Glass API key.
    
    Returns:
        dict: Astronomical data or error message.
    """
    # Default API key if none provided
    if not api_key:
        api_key = "ad33d24a-0bd7-11f0-803a-0242ac130003-ad33d2a4-0bd7-11f0-803a-0242ac130003"
        
    url = f"https://api.stormglass.io/v2/astronomy/point?lat={lat}&lng={lon}"
    headers = {"Authorization": api_key}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()["data"][0]  # First entry for the current day
            return {
                "sunrise": data["sunrise"],
                "sunset": data["sunset"],
                "moonrise": data["moonrise"],
                "moonset": data["moonset"],
                "moon_phase": data["moonPhase"],
                "status": "success"
            }
        return {"error": f"Failed to fetch astronomy data: {response.status_code} - {response.text}", "status": "error"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request error: {e}", "status": "error"}


def get_weather_data(lat, lon):
    """
    Get weather data for a specific location.
    This is a placeholder function that would normally call a weather API.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        
    Returns:
        dict: Weather data
    """
    # This is a placeholder. In a real application, you would call a weather API
    # For now, we'll return mock data
    try:
        # You could replace this with a real API call
        # Example: OpenWeatherMap, WeatherAPI, etc.
        return {
            "temperature": 25,  # Celsius
            "feels_like": 27,
            "humidity": 65,  # Percentage
            "wind_speed": 15,  # km/h
            "wind_direction": "NE",
            "pressure": 1015,  # hPa
            "description": "Partly cloudy",
            "icon": "cloud-sun",
            "status": "success"
        }
    except Exception as e:
        return {"error": f"Error getting weather data: {e}", "status": "error"}


def get_client_location_data():
    """
    Get comprehensive location-based data for the client.
    
    Returns:
        dict: Combined data including location, time, weather, and astronomy
    """
    # Get client location
    location = get_location()
    if not location:
        return {"error": "Could not determine location", "status": "error"}
    
    lat, lon = location
    
    # Get local time
    time_data = get_local_time(lat, lon)
    if "error" in time_data:
        return {"error": time_data["error"], "status": "error"}
    
    # Get weather data
    weather_data = get_weather_data(lat, lon)
    
    # Get astronomy data
    astro_data = get_stormglass_astronomy(lat, lon)
    
    # Combine all data
    return {
        "location": {
            "latitude": lat,
            "longitude": lon
        },
        "time": time_data,
        "weather": weather_data,
        "astronomy": astro_data,
        "status": "success"
    }


# Example usage
if __name__ == "__main__":
    client_data = get_client_location_data()
    print(client_data)
import geocoder

def get_device_location():
    """Retrieve the current GPS coordinates of the device using IP-based geolocation.
    
    Returns:
        dict: {'lat': float, 'lon': float} with latitude and longitude.
    """
    try:
        # Use IP-based geolocation
        g = geocoder.ip('me')
        if g.ok:
            return {"lat": g.lat, "lon": g.lng}
        else:
            print("IP geolocation failed. Using fallback coordinates (Tunis).")
            return {"lat": 36.8065, "lon": 10.1815}
    except Exception as e:
        print(f"Error getting location: {e}")
        return {"lat": 36.8065, "lon": 10.1815}
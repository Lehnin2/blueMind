
import folium
import webbrowser
import os

def get_map_location():
    """Display an interactive map of Tunisia and return coordinates of a clicked point.
    
    Returns:
        dict: {'lat': float, 'lon': float} with latitude and longitude.
    """
    try:
        # Create map centered on Tunisia (Tunis)
        m = folium.Map(location=[36.8065, 10.1815], zoom_start=8)
        
        # Add click event to show coordinatesAA
        m.add_child(folium.LatLngPopup())
        
        # Save map as HTML
        map_file = "tunisia_map.html"
        m.save(map_file)
        
        # Open map in browser
        webbrowser.open(f"file://{os.path.abspath(map_file)}")
        print("Map opened in browser. Click a point to see coordinates in the popup.")
        print("Then, enter the coordinates below.")
        
        # Prompt user to input coordinates from popup
        try:
            lat = float(input("Enter the clicked latitude: "))
            lon = float(input("Enter the clicked longitude: "))
            return {"lat": lat, "lon": lon}
        except ValueError:
            print("Invalid input. Using fallback coordinates (Tunis).")
            return {"lat": 36.8065, "lon": 10.1815}
    except Exception as e:
        print(f"Error with map: {e}")
        return {"lat": 36.8065, "lon": 10.1815}


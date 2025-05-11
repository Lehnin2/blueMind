from flask import Blueprint, jsonify, request
from app.tools.astronomy_weather import get_weather_data, get_stormglass_astronomy

astro_weather_api = Blueprint('astro_weather_api', __name__)

@astro_weather_api.route('/api/astro-weather')
def get_astro_weather_data():
    """API endpoint to get astronomy and weather data based on client location."""
    # Get location from query parameters
    try:
        lat = float(request.args.get('lat', 0))
        lon = float(request.args.get('lon', 0))
        
        # Get weather and astronomy data
        weather_data = get_weather_data(lat, lon)
        # Récupérer la clé API StormGlass si elle est fournie
        api_key = request.args.get('api_key', "ad33d24a-0bd7-11f0-803a-0242ac130003-ad33d2a4-0bd7-11f0-803a-0242ac130003")
        astronomy_data = get_stormglass_astronomy(lat, lon, api_key)
        
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
            'timestamp': request.args.get('_', '0')  # Include timestamp from request to prevent caching
        }
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            'error': f'Error fetching astronomy and weather data: {str(e)}',
            'status': 'error'
        }), 500
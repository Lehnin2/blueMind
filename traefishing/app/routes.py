# Update the current_location route to use the new create_location_map function
@app.route('/current-location')
def current_location():
    location = get_current_location()
    # Convert the map to HTML
    map_html = location["map"]._repr_html_()
    return render_template('location.html', location=location, map=map_html)

# Add route for client location data (weather and astronomy)
@app.route('/api/client-data')
def client_location_data():
    """API endpoint for client location-based data (weather, time, astronomy)"""
    try:
        # Get lat/lon from query parameters if provided
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        from app.tools.astronomy_weather import get_client_location_data, get_local_time, get_stormglass_astronomy, get_weather_data
        
        if lat and lon:
            # Use provided coordinates
            lat = float(lat)
            lon = float(lon)
            
            # Get time data based on coordinates
            time_data = get_local_time(lat, lon)
            
            # Get weather data
            weather_data = get_weather_data(lat, lon)
            
            # Get astronomy data
            astro_data = get_stormglass_astronomy(lat, lon)
            
            # Combine all data
            data = {
                "location": {
                    "latitude": lat,
                    "longitude": lon
                },
                "time": time_data,
                "weather": weather_data,
                "astronomy": astro_data,
                "status": "success"
            }
        else:
            # Use IP-based geolocation
            data = get_client_location_data()
            
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


# Add these imports at the top of your routes.py file
from flask import jsonify, request, render_template
from app.agent_router import AgentRouter

# Initialize the agent router (which manages both chatbot and maritime agents)
agent_router = AgentRouter()

# Add these routes to your routes.py file
# Make sure this route is defined in your routes.py file
@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    """API endpoint for the chatbot"""
    data = request.json
    message = data.get('message', '')
    use_voice = data.get('voice', False)
    force_maritime = data.get('force_maritime', False)
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    response = agent_router.handle_message(message, use_voice, force_maritime)
    return jsonify(response)

@app.route('/api/chatbot/listen', methods=['GET'])
def chatbot_listen():
    """API endpoint for voice input"""
    try:
        text = agent_router.listen()
        return jsonify({'text': text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/maritime-agent', methods=['POST'])
def maritime_agent_api():
    """API endpoint specifically for the maritime agent"""
    data = request.json
    message = data.get('message', '')
    use_voice = data.get('voice', False)
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Force the use of the maritime agent
    response = agent_router.handle_message(message, use_voice, force_maritime=True)
    return jsonify(response)
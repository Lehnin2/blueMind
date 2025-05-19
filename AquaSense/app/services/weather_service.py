import aiohttp
from datetime import datetime
from config.settings import WEATHER_API_KEY

class WeatherService:
    BASE_URL = "http://api.weatherapi.com/v1"
    _cache = {}
    _cache_duration = 300  # 5 minutes

    @staticmethod
    def _is_cache_valid(cache_time):
        return (datetime.now() - cache_time).total_seconds() < WeatherService._cache_duration

    @staticmethod
    async def get_current_weather(coordinates: str):
        try:
            print(f"Tentative de récupération de la météo pour les coordonnées: {coordinates}")
            print(f"Clé API utilisée: {WEATHER_API_KEY[:5]}...")  # Affiche les 5 premiers caractères de la clé
            
            if not WEATHER_API_KEY:
                raise ValueError("WEATHER_API_KEY n'est pas configurée")

            # Decode URL-encoded coordinates
            decoded_coordinates = coordinates.replace('%2C', ',')
            print(f"Coordonnées décodées: {decoded_coordinates}")
            
            cache_key = f"current_{decoded_coordinates}"
            if cache_key in WeatherService._cache:
                data, cache_time = WeatherService._cache[cache_key]
                if WeatherService._is_cache_valid(cache_time):
                    return data

            url = f"{WeatherService.BASE_URL}/current.json"
            params = {
                'key': WEATHER_API_KEY,
                'q': decoded_coordinates,
                'aqi': 'no'
            }
            print(f"URL de l'API: {url}")
            print(f"Paramètres: {params}")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    print(f"Statut de la réponse: {response.status}")
                    if response.status == 404:
                        return None
                    response.raise_for_status()
                    data = await response.json()
                    print(f"Réponse de l'API: {data}")

            fishing_info = WeatherService.analyze_fishing(data)
            result = {
                'temperature': data['current']['temp_c'],
                'condition': data['current']['condition']['text'],
                'humidity': data['current']['humidity'],
                'wind_speed': data['current']['wind_kph'],
                'wind_dir': data['current']['wind_dir'],
                'feels_like': data['current']['feelslike_c'],
                'visibility': data['current']['vis_km'],
                'last_updated': data['current']['last_updated'],
                'location': {
                    'name': data['location']['name'],
                    'region': data['location']['region'],
                    'country': data['location']['country']
                },
                'fishing': fishing_info
            }

            # Cache the result
            WeatherService._cache[cache_key] = (result, datetime.now())
            return result

        except Exception as e:
            print(f"Erreur détaillée lors de la récupération des données météo: {str(e)}")
            print(f"Type d'erreur: {type(e).__name__}")
            raise

    @staticmethod
    async def get_forecast(coordinates: str, days: int = 3):
        try:
            # Decode URL-encoded coordinates
            decoded_coordinates = coordinates.replace('%2C', ',')
            
            url = f"{WeatherService.BASE_URL}/forecast.json"
            params = {
                'key': WEATHER_API_KEY,
                'q': decoded_coordinates,
                'days': days,
                'aqi': 'no',
                'alerts': 'no'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 404:
                        return None
                    response.raise_for_status()
                    data = await response.json()

            forecast = []
            for day in data['forecast']['forecastday']:
                forecast.append({
                    'date': day['date'],
                    'max_temp': day['day']['maxtemp_c'],
                    'min_temp': day['day']['mintemp_c'],
                    'avg_temp': day['day']['avgtemp_c'],
                    'condition': day['day']['condition']['text'],
                    'chance_of_rain': day['day']['daily_chance_of_rain'],
                    'sunrise': day['astro']['sunrise'],
                    'sunset': day['astro']['sunset'],
                    'hourly': [{
                        'time': hour['time'].split()[1],
                        'temp': hour['temp_c'],
                        'condition': hour['condition']['text'],
                        'chance_of_rain': hour['chance_of_rain']
                    } for hour in day['hour']]
                })

            return {
                'location': {
                    'name': data['location']['name'],
                    'region': data['location']['region'],
                    'country': data['location']['country']
                },
                'forecast': forecast
            }

        except Exception as e:
            print(f"Weather forecast error: {e}")
            return None

    @staticmethod
    def analyze_fishing(weather_data):
        if not weather_data or 'current' not in weather_data:
            return None

        current = weather_data['current']
        condition = current['condition']['text'].lower()
        temperature = current['temp_c']
        wind_speed = current['wind_kph']
        visibility = current['vis_km']

        reasons = []
        can_fish = True

        if temperature < 10 or temperature > 30:
            can_fish = False
            reasons.append(f"Température non idéale ({temperature}°C)")

        if wind_speed > 25:
            can_fish = False
            reasons.append(f"Vent trop fort ({wind_speed} km/h)")

        if 'rain' in condition or 'storm' in condition or 'thunder' in condition:
            can_fish = False
            reasons.append(f"Mauvais temps: {condition}")

        if visibility < 5:
            can_fish = False
            reasons.append(f"Visibilité réduite ({visibility} km)")

        if can_fish and not reasons:
            reasons.append("Conditions parfaites pour la pêche !")

        return {
            'can_fish': can_fish,
            'reasons': reasons,
            'temperature': temperature,
            'wind_speed': wind_speed,
            'condition': current['condition']['text'],
            'visibility': visibility
        }
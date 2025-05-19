import aiohttp
from datetime import datetime
from config import settings

class AstronomyService:
    BASE_URL = "https://api.nasa.gov/planetary/apod"

    @staticmethod
    async def get_astronomy_picture():
        if not hasattr(settings, 'NASA_API_KEY') or not settings.NASA_API_KEY:
            print("Erreur : NASA_API_KEY non configurée")
            return None

        params = {
            'api_key': settings.NASA_API_KEY,
            'thumbs': True
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(AstronomyService.BASE_URL, params=params, timeout=10) as response:
                    if response.status == 403:
                        print("Erreur : Clé API NASA invalide")
                        return None
                    response.raise_for_status()
                    data = await response.json()

                    return {
                        'title': data.get('title', 'Astronomy Picture of the Day'),
                        'explanation': data.get('explanation', ''),
                        'media_url': data.get('url') or data.get('thumbnail_url'),
                        'media_type': data.get('media_type', 'image'),
                        'date': data.get('date', datetime.today().strftime('%Y-%m-%d')),
                        'copyright': data.get('copyright', 'Public Domain')
                    }
        except aiohttp.ClientError as e:
            print(f"Erreur de connexion à l'API NASA : {e}")
            return None
        except Exception as e:
            print(f"Erreur inattendue de l'API NASA : {e}")
            return None
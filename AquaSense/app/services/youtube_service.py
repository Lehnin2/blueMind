import googleapiclient.discovery
import googleapiclient.errors
from configz import settings
from app.core.schemas import FishResponse
from typing import List, Dict, Union
from groq import Groq

groq_client = Groq(api_key=settings.GROQ_API_KEY)

def generate_cooking_query(fish_name: str, recipe_name: str = None) -> str:
    try:
        if recipe_name:
            prompt = (
                f"Given the fish name '{fish_name}' and recipe '{recipe_name}', generate a concise YouTube search query "
                "to find a video on how to make this specific dish. The query should be in English and include both "
                "the recipe name and fish name. Return only the query string, nothing else."
            )
        else:
            prompt = (
                f"Given the fish name '{fish_name}', generate a concise YouTube search query to find a video "
                "on how to cook this fish. The query should be in English, start with 'how to cook', and include "
                "the fish name. Return only the query string, nothing else."
            )
            
        response = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates precise search queries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.3
        )
        query = response.choices[0].message.content.strip()
        
        if recipe_name:
            if not (recipe_name.lower() in query.lower() and fish_name.lower() in query.lower()):
                return f"how to make {recipe_name} with {fish_name}"
        else:
            if not query.lower().startswith("how to cook"):
                return f"how to cook {fish_name}"
                
        return query
    except Exception as e:
        print(f"Error generating query with Groq: {e}")
        return f"how to make {recipe_name} with {fish_name}" if recipe_name else f"how to cook {fish_name}"

def youtube_search(fish_data: Union[Dict, str], max_results: int = 1, recipe_name: str = None) -> Dict:
    try:
        if isinstance(fish_data, str):
            fish_name = fish_data
        elif isinstance(fish_data, dict):
            fish_name = (
                fish_data.get("nom_francais") or
                fish_data.get("nom_tunisien") or
                fish_data.get("nom_scientifique") or
                "unknown fish"
            )
        else:
            fish_name = "unknown fish"
        
        query = generate_cooking_query(fish_name, recipe_name)
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)
        
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=max_results
        )
        response = request.execute()
        
        for item in response.get("items", []):
            return {
                "title": item["snippet"]["title"],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            }
        
        return {}
    except googleapiclient.errors.HttpError as e:
        print(f"YouTube API error: {e}")
        error_reason = e.error_details[0].get("reason") if hasattr(e, "error_details") and e.error_details else "Unknown"
        if "forbidden" in str(e).lower():
            print(f"YouTube API blocked: {error_reason}. Check Google Cloud Console.")
        return {}
    except Exception as e:
        print(f"Unexpected error in youtube_search: {e}")
        return {}

def add_videos_to_recipes(fish_data: FishResponse, max_videos_per_recipe: int = 1) -> FishResponse:
    if not fish_data.recipe_suggestions:
        print(f"No recipe suggestions for {fish_data.nom_francais or fish_data.nom_scientifique or 'Unknown'}")
        return fish_data
        
    try:
        for recipe in fish_data.recipe_suggestions:
            recipe_name = recipe.get('name')  # Use get() for safety
            fish_name = fish_data.nom_francais or fish_data.nom_tunisien or fish_data.nom_scientifique or ""
            
            if recipe_name and fish_name:
                print(f"Searching YouTube for recipe: {recipe_name} with {fish_name}")
                video = youtube_search(fish_name, max_results=max_videos_per_recipe, recipe_name=recipe_name)
                recipe['video'] = video  # Use dict access for compatibility
            else:
                print(f"Skipping YouTube search: missing recipe_name or fish_name")
                recipe['video'] = {}
    
        return fish_data
    except Exception as e:
        print(f"Error in add_videos_to_recipes: {e}")
        for recipe in fish_data.recipe_suggestions:
            recipe['video'] = {}
        return fish_data
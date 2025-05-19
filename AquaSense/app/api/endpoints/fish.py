from fastapi import APIRouter, Depends, HTTPException
from app.core.schemas import FishQuery, SearchResponse, FishResponse
from app.services.search_service import search_fish
from app.services.llm_service import correct_query_with_groq, improve_results_with_groq
from app.services.youtube_service import youtube_search, add_videos_to_recipes
from typing import List
from configz import settings

router = APIRouter()

@router.post("/search", response_model=SearchResponse, summary="Search for fish by name")
async def search(query: FishQuery):
    try:
        corrected_query = correct_query_with_groq(query.query)
        results = search_fish(corrected_query, query.top_k)
        fish_results = [FishResponse(**item) for item in results]
        
        if query.enhance_with_llm:
            fish_results = improve_results_with_groq(fish_results)
        
        for fish in fish_results:
            query_name = fish.nom_tunisien or fish.nom_francais or fish.nom_scientifique or ""
            if query_name:
                try:
                    fish.video = youtube_search(query_name)
                except Exception as e:
                    print(f"Error fetching main video for {query_name}: {e}")
                    fish.video = {}
            
            if fish.recipe_suggestions:
                try:
                    add_videos_to_recipes(fish)
                except Exception as e:
                    print(f"Error adding recipe videos for {query_name}: {e}")
        
        return SearchResponse(
            corrected_query=corrected_query,
            results=fish_results,
            count=len(fish_results)
        )
    except Exception as e:
        print(f"Search endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/all", response_model=List[FishResponse], summary="Get all fish")
async def get_all_fish():
    from core.models import get_fish_data
    
    try:
        fish_data = get_fish_data()
        return [FishResponse(**item) for item in fish_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
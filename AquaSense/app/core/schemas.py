from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class FishQuery(BaseModel):
    """Schema for fish search query"""
    query: str = Field(..., description="Fish name or search term")
    top_k: int = Field(1, description="Number of results to return")
    enhance_with_llm: bool = Field(True, description="Whether to enhance results with LLM")

class FishBase(BaseModel):
    """Base schema for fish data"""
    nom_tunisien: Optional[str] = Field(None, description="Tunisian name")
    nom_francais: Optional[str] = Field(None, description="French name")
    nom_scientifique: Optional[str] = Field(None, description="Scientific name")
    protected: bool = Field(False, description="Protected status")
    invasive: bool = Field(False, description="Invasive status")

class Recipe(BaseModel):
    """Schema for recipe data"""
    name: str = Field(..., description="Recipe name")
    description: str = Field(..., description="Brief recipe description")
    video: Optional[Dict[str, str]] = Field(None, description="YouTube video information")

class FishResponse(FishBase):
    """Response schema for fish data with enhanced description, recipes and video"""
    improved_description: Optional[str] = Field(None, description="LLM-enhanced description")
    video: Optional[Dict[str, str]] = Field(None, description="YouTube video information")
    recipe_suggestions: List[Recipe] = Field(default_factory=list, description="Recipe suggestions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nom_tunisien": "وراطة",
                "nom_francais": "Dorade royale",
                "nom_scientifique": "Sparus aurata",
                "protected": False,
                "invasive": False,
                "improved_description": "La Dorade royale (Sparus aurata) est un poisson marin de la famille des Sparidés...",
                "video": {
                    "title": "Dorade Royale - Fish Description",
                    "url": "https://www.youtube.com/watch?v=example"
                },
                "recipe_suggestions": [
                    {
                        "name": "Dorade royale grillée",
                        "description": "Dorade grillée avec herbes et citron",
                        "video": {
                            "title": "How to make grilled Dorade royale",
                            "url": "https://www.youtube.com/watch?v=example"
                        }
                    }
                ]
            }
        }

class SearchResponse(BaseModel):
    """Schema for search response"""
    corrected_query: str = Field(..., description="Query after correction")
    results: List[FishResponse] = Field(..., description="Search results")
    count: int = Field(..., description="Number of results")

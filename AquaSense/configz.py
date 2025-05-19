import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # API configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Fish Information API"
    
    # Groq API key
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY2", "")
    # YouTube API key
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
    # Model settings
    EMBEDDING_MODEL: str = "distiluse-base-multilingual-cased-v2"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_MODEL_DESCRIPTION: str = "llama3-70b-8192"
    
    # Data paths
    DATA_PATH: str = os.getenv("DATA_PATH", "data/merged_1_3.json")
    
    # Search settings
    DEFAULT_TOP_K: int = 3

settings = Settings()
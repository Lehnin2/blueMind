from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    WEATHER_API_KEY: str = ""  # Your WeatherAPI key
    NASA_API_KEY: str = ""     # Your NASA API key

    class Config:
        env_file = ".env"

settings = Settings()
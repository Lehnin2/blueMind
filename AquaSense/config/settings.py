import os
from dotenv import load_dotenv
import logging

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Chargement du fichier .env
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
env_path = os.path.join(project_root, '.env')
logger.debug(f"Tentative de chargement du fichier .env depuis: {env_path}")
logger.debug(f"Le fichier .env existe: {os.path.exists(env_path)}")

if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.debug("Fichier .env chargé avec succès")
    # Vérification du contenu du fichier .env
    with open(env_path, 'r') as f:
        env_content = f.read()
        logger.debug(f"Contenu du fichier .env: {env_content}")
else:
    logger.error("Fichier .env non trouvé!")

# Configuration de l'application
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8001"))

# Configuration Supabase
SUPABASE_URL = "https://yrbvvkfvmhtjgovziiai.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlyYnZ2a2Z2bWh0amdvdnppaWFpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYyMDI5NjEsImV4cCI6MjA2MTc3ODk2MX0.MafN8wVQyXJ-ciwPi5LePbVegNYJr_vtL-v9vk7bTsE"

# Configuration de la base de données
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Configuration des clés secrètes
SECRET_KEY = os.getenv("SECRET_KEY", "votre_cle_secrete_ici")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Configuration WeatherAPI
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "a25c363bab634f54a56210057251704")
logger.debug(f"WEATHER_API_KEY chargée: {WEATHER_API_KEY[:5] if WEATHER_API_KEY else 'Non configurée'}")
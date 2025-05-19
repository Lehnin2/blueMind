import os
from dotenv import load_dotenv
from app.config import settings

load_dotenv()

# Configuration de l'application
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

# Configuration Supabase
SUPABASE_URL = "https://yrbvvkfvmhtjgovziiai.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlyYnZ2a2Z2bWh0amdvdnppaWFpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYyMDI5NjEsImV4cCI6MjA2MTc3ODk2MX0.MafN8wVQyXJ-ciwPi5LePbVegNYJr_vtL-v9vk7bTsE"

# Configuration de la base de données
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Configuration des clés secrètes
SECRET_KEY = os.getenv("SECRET_KEY", "votre_cle_secrete_ici")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 
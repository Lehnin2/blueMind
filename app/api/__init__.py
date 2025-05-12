# Package API pour l'application d'assistance réglementaire pêche

from fastapi import APIRouter
from app.api.routes import router as api_router

# Création du router principal
router = APIRouter()

# Inclusion des routes API
router.include_router(api_router)
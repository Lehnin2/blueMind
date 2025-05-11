from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app):
    """Configure CORS pour l'application avec support SSE"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # À remplacer par les domaines autorisés en production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Type", "Content-Length", "Cache-Control"]
    )
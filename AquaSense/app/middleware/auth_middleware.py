from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from app.config.supabase import supabase
import logging

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request, call_next):
    # Liste des routes publiques qui ne nécessitent pas d'authentification
    public_routes = ["/", "/login", "/signup", "/static"]
    
    # Vérifier si la route actuelle est publique
    if any(request.url.path.startswith(route) for route in public_routes):
        return await call_next(request)
    
    # Récupérer le token du cookie
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        logger.debug("Pas de token trouvé, redirection vers /login")
        return RedirectResponse(url="/login", status_code=303)
    
    try:
        logger.debug("Vérification du token avec Supabase")
        # Vérifier la validité du token avec Supabase
        user = supabase.auth.get_user(access_token)
        if not user:
            logger.debug("Token invalide, redirection vers /login")
            return RedirectResponse(url="/login", status_code=303)
        
        # Ajouter l'utilisateur à la requête pour utilisation ultérieure
        request.state.user = user
        return await call_next(request)
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du token: {str(e)}")
        return RedirectResponse(url="/login", status_code=303) 
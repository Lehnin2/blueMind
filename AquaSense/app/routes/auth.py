from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.config.supabase import supabase
from typing import Optional
from fastapi import Response
import json
import logging

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    try:
        logger.debug(f"Tentative de connexion pour l'email: {email}")
        
        # Tentative de connexion avec Supabase
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        logger.debug(f"Réponse brute de Supabase: {auth_response}")
        
        # Vérification de la réponse
        if auth_response and hasattr(auth_response, 'session'):
            logger.debug("Connexion réussie, redirection vers /index")
            
            # Création de la réponse de redirection
            response = RedirectResponse(url="/index", status_code=303)
            
            # Stockage du token dans un cookie
            response.set_cookie(
                key="access_token",
                value=auth_response.session.access_token,
                httponly=True,
                secure=False,  # Mettre à True en production
                samesite="lax"
            )
            
            return response
        else:
            logger.error(f"Réponse invalide de Supabase: {auth_response}")
            raise HTTPException(
                status_code=400,
                detail="Email ou mot de passe incorrect"
            )
    except Exception as e:
        logger.error(f"Erreur détaillée de connexion: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Erreur de connexion: {str(e)}"
        )

@router.post("/signup")
async def signup(email: str = Form(...), password: str = Form(...)):
    try:
        logger.debug(f"Tentative d'inscription pour l'email: {email}")
        
        # Tentative d'inscription avec Supabase
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        logger.debug(f"Réponse brute de Supabase pour l'inscription: {auth_response}")
        
        if auth_response and hasattr(auth_response, 'user'):
            logger.debug("Inscription réussie, redirection vers /login")
            return RedirectResponse(url="/login", status_code=303)
        else:
            logger.error(f"Réponse invalide de Supabase pour l'inscription: {auth_response}")
            raise HTTPException(
                status_code=400,
                detail="Erreur lors de l'inscription"
            )
    except Exception as e:
        logger.error(f"Erreur détaillée d'inscription: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Erreur lors de l'inscription: {str(e)}"
        ) 
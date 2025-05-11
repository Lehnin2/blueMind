from fastapi import APIRouter, Request, Response, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import os
from pathlib import Path
from typing import Optional
from .supabase_client import SupabaseClient

# Créer un router pour les routes d'authentification
router = APIRouter()

# Initialiser le client Supabase
supabase = SupabaseClient()

# Configurer les templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Système de sécurité basique
security = HTTPBasic()

# Routes pour l'authentification
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Afficher la page de connexion"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Afficher la page d'inscription"""
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/api/login")
async def login(request: Request):
    """API pour la connexion d'un utilisateur"""
    try:
        data = await request.json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JSONResponse({"error": "Email et mot de passe requis"}, status_code=400)
        
        # Authentifier l'utilisateur via Supabase
        response = supabase.login(email, password)
        
        if "error" in response:
            return JSONResponse({"error": response["error"]}, status_code=401)
        
        # Créer un cookie pour stocker le token d'authentification
        access_token = response.get("access_token")
        refresh_token = response.get("refresh_token")
        
        resp = JSONResponse({"success": True, "user": response.get("user")})
        resp.set_cookie(key="access_token", value=access_token, httponly=True, max_age=3600)
        resp.set_cookie(key="refresh_token", value=refresh_token, httponly=True, max_age=7*24*3600)
        
        return resp
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/api/register")
async def register(request: Request):
    """API pour l'inscription d'un nouvel utilisateur"""
    try:
        data = await request.json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JSONResponse({"error": "Email et mot de passe requis"}, status_code=400)
        
        # Vérifier la complexité du mot de passe
        if len(password) < 8:
            return JSONResponse({"error": "Le mot de passe doit contenir au moins 8 caractères"}, status_code=400)
        
        # Enregistrer l'utilisateur via Supabase
        response = supabase.register(email, password)
        
        if "error" in response:
            return JSONResponse({"error": response["error"]}, status_code=400)
        
        return JSONResponse({"success": True, "message": "Inscription réussie. Vous pouvez maintenant vous connecter."})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/api/logout")
async def logout(request: Request):
    """API pour la déconnexion d'un utilisateur"""
    try:
        # Récupérer le token d'authentification depuis le cookie
        access_token = request.cookies.get("access_token")
        
        if not access_token:
            return JSONResponse({"error": "Non authentifié"}, status_code=401)
        
        # Déconnecter l'utilisateur via Supabase
        supabase.logout(access_token)
        
        # Supprimer les cookies d'authentification
        resp = JSONResponse({"success": True})
        resp.delete_cookie(key="access_token")
        resp.delete_cookie(key="refresh_token")
        
        return resp
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
# Routes API pour l'application d'assistance réglementaire pêche

from fastapi import APIRouter, Request, Depends, HTTPException, status, Form, File, UploadFile
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import json

# Import des agents
from app.agents.user_interaction_agent import UserInteractionAgent
from app.agents.community_agent import CommunityAgent
from app.agents.reasoning_agent import ReasoningAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.generation_agent import GenerationAgent
from app.agents.report_generation_agent import ReportGenerationAgent
from app.agents.web_search_agent import WebSearchAgent

# Création du router
router = APIRouter(prefix="/api", tags=["api"])

# Initialisation des agents
reasoning_agent = ReasoningAgent()
retrieval_agent = RetrievalAgent()
generation_agent = GenerationAgent()
report_generation_agent = ReportGenerationAgent()
user_interaction_agent = UserInteractionAgent(reasoning_agent=reasoning_agent, generation_agent=generation_agent)
community_agent = CommunityAgent(reasoning_agent=reasoning_agent)
web_search_agent = WebSearchAgent()

# Middleware pour vérifier l'authentification API
async def verify_api_key(request: Request):
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != "test_api_key":  # À remplacer par une vérification sécurisée
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide ou manquante"
        )
    return True

# Routes pour les requêtes utilisateur
@router.post("/query")
async def process_query(request: Request, query: str = Form(...), user_id: Optional[str] = Form(None)):
    """Traite une requête textuelle de l'utilisateur"""
    try:
        response = user_interaction_agent.process_query(query, user_profile={"user_id": user_id} if user_id else None)
        return response
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Erreur lors du traitement de la requête: {str(e)}"})

# Route pour le chat
@router.post("/chat")
async def chat_message(request: Request, message: str = Form(...), conversation_id: Optional[str] = Form(None)):
    """Traite un message de chat et renvoie une réponse"""
    try:
        # Utiliser l'agent d'interaction utilisateur pour traiter le message
        response = user_interaction_agent.process_query(message)
        return response
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Erreur lors du traitement du message: {str(e)}"})

# Route pour la recherche web DeepSearch
@router.post("/web-search")
async def web_search(request: Request, query: str = Form(...), language: str = Form("fr")):
    """Effectue une recherche web via l'API xAI DeepSearch"""
    try:
        # Utiliser l'agent de recherche web pour effectuer la recherche
        response = await web_search_agent.search(query, language)
        return response
    except HTTPException as e:
        # Propager l'exception HTTP telle quelle
        raise e
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Erreur lors de la recherche web: {str(e)}"})

# Route pour la génération de rapports
@router.post("/generate-report")
async def generate_report(request: Request, report_type: str = Form(...), parameters: str = Form(...)):
    """Génère un rapport personnalisé"""
    try:
        # Convertir les paramètres JSON en dictionnaire
        params_dict = json.loads(parameters)
        
        # Utiliser l'agent de génération de rapports
        report = report_generation_agent.generate_report(report_type, params_dict)
        return report
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Erreur lors de la génération du rapport: {str(e)}"})

# Routes pour les contributions communautaires
@router.post("/contributions/submit")
async def submit_contribution(request: Request, contribution_type: str = Form(...), data: str = Form(...), user_id: Optional[str] = Form(None)):
    """Soumet une nouvelle contribution communautaire"""
    try:
        # Convertir les données JSON en dictionnaire
        contribution_data = json.loads(data)
        contribution_data["type"] = contribution_type
        
        # Soumettre la contribution via l'agent communautaire
        result = community_agent.submit_contribution(contribution_data, user_id)
        return result
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Erreur lors de la soumission de la contribution: {str(e)}"})

@router.get("/contributions/pending")
async def get_pending_contributions(request: Request, limit: int = 10):
    """Récupère les contributions en attente de validation"""
    try:
        # Récupérer les contributions en attente via l'agent communautaire
        pending = community_agent.get_pending_contributions(limit)
        return {"pending_contributions": pending}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Erreur lors de la récupération des contributions: {str(e)}"})

@router.post("/contributions/validate/{contribution_id}")
async def validate_contribution(request: Request, contribution_id: str, validator_id: Optional[str] = Form(None)):
    """Valide une contribution en attente"""
    try:
        # Valider la contribution via l'agent communautaire
        result = community_agent.validate_contribution(contribution_id, validator_id)
        return result
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Erreur lors de la validation de la contribution: {str(e)}"})

@router.get("/contributions/statistics")
async def get_contribution_statistics(request: Request):
    """Récupère des statistiques sur les contributions"""
    try:
        # Récupérer les statistiques via l'agent communautaire
        stats = community_agent.get_contribution_statistics()
        return stats
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Erreur lors de la récupération des statistiques: {str(e)}"})

# Route pour la recherche
@router.get("/search")
async def search(request: Request, query: str, filters: Optional[str] = None):
    """Recherche dans la base de connaissances"""
    try:
        # Convertir les filtres JSON en dictionnaire si fournis
        filters_dict = json.loads(filters) if filters else None
        
        # Utiliser l'agent de récupération pour effectuer la recherche
        results = retrieval_agent.search(query, filters_dict)
        return {"results": results}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Erreur lors de la recherche: {str(e)}"})
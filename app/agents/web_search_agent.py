# Agent de recherche web (Web Search Agent)
# Responsable de la recherche d'informations sur le web via l'API xAI DeepSearch

import os
import httpx
from typing import Dict, List, Any, Optional
from fastapi import HTTPException

class WebSearchAgent:
    """
    Agent responsable de la recherche d'informations sur le web via l'API xAI DeepSearch.
    
    Cet agent est chargé d'effectuer des recherches web pour compléter les informations
    disponibles localement, en utilisant l'API xAI avec le modèle Grok-3.
    """
    
    def __init__(self, api_key=None):
        """
        Initialise l'agent de recherche web.
        
        Args:
            api_key (str, optional): Clé API pour xAI DeepSearch
        """
        # Utiliser la clé API fournie ou celle de l'environnement
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("La clé API XAI_API_KEY n'est pas définie. Veuillez la définir dans un fichier .env à la racine du projet.")
        self.search_history = []
    
    async def search(self, query: str, language: str = "fr"):
        """
        Effectue une recherche web via l'API xAI DeepSearch.
        
        Args:
            query (str): Requête de recherche
            language (str, optional): Langue de la requête (fr, en, etc.)
            
        Returns:
            dict: Résultats de la recherche avec sources et suggestions
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    json={
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a web search agent using DeepSearch mode. Provide a concise response with sources for the query."
                            },
                            {
                                "role": "user",
                                "content": f"Search for: {query}"
                            }
                        ],
                        "model": "grok-3-latest",
                        "stream": False,
                        "temperature": 0
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                response.raise_for_status()  # Vérifie les erreurs HTTP
                data = response.json()
                
                # Enregistrer la recherche dans l'historique
                self.search_history.append({"query": query, "language": language})
                
                return {
                    "response": data["choices"][0]["message"]["content"],
                    "sources": data.get("sources", []),
                    "suggestions": ["Faire un quiz", "Contribuer"],
                    "warning": None
                }
                
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur API xAI: {str(e)}"
            )
        except Exception as e:
            return {
                "response": "Erreur lors de la recherche Web. Contactez la DGPA.",
                "sources": [],
                "suggestions": ["Faire un quiz", "Contribuer"],
                "warning": f"Erreur: {str(e)}"
            }
    
    def get_search_history(self, limit: int = 10):
        """
        Récupère l'historique des recherches.
        
        Args:
            limit (int, optional): Nombre maximum de recherches à récupérer
            
        Returns:
            list: Historique des recherches
        """
        return self.search_history[-limit:]
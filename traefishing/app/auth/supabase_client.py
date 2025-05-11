import os
import json
import requests
from typing import Dict, Optional, Any
from pathlib import Path

class SupabaseClient:
    """
    Client pour interagir avec l'API Supabase pour l'authentification
    """
    
    def __init__(self):
        """Initialiser le client Supabase avec les clés API depuis la configuration"""
        config_path = Path(__file__).parent.parent / 'config' / 'api_keys.json'
        try:
            with open(config_path) as f:
                config = json.load(f)
                self.supabase_url = config.get('SUPABASE_URL', '')
                self.supabase_key = config.get('SUPABASE_KEY', '')
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Erreur lors du chargement des clés Supabase: {e}")
            self.supabase_url = ''
            self.supabase_key = ''
            
        self.headers = {
            "apikey": self.supabase_key,
            "Content-Type": "application/json"
        }
    
    def register(self, email: str, password: str) -> Dict[str, Any]:
        """Enregistrer un nouvel utilisateur"""
        try:
            url = f"{self.supabase_url}/auth/v1/signup"
            payload = {
                "email": email,
                "password": password
            }
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Connecter un utilisateur existant"""
        try:
            # URL correcte pour l'authentification Supabase
            url = f"{self.supabase_url}/auth/v1/token"
            
            # Paramètres de requête pour spécifier le type d'authentification
            params = {"grant_type": "password"}
            
            # Données d'authentification
            payload = {
                "email": email,
                "password": password
            }
            
            # Afficher les informations de débogage
            print(f"Tentative de connexion pour {email} à {url}")
            print(f"Headers: {self.headers}")
            
            # Effectuer la requête d'authentification
            response = requests.post(url, headers=self.headers, json=payload, params=params)
            
            # Afficher la réponse complète pour le débogage
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code != 200:
                error_data = response.json()
                error_msg = error_data.get("error_description", error_data.get("msg", "Erreur de connexion"))
                print(f"Erreur de connexion: {error_msg}, Status: {response.status_code}")
                return {"error": error_msg}
                
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Exception lors de la connexion: {str(e)}")
            return {"error": "Erreur de connexion au serveur"}
    
    def logout(self, access_token: str) -> Dict[str, Any]:
        """Déconnecter un utilisateur"""
        try:
            url = f"{self.supabase_url}/auth/v1/logout"
            headers = self.headers.copy()
            headers["Authorization"] = f"Bearer {access_token}"
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            return {"success": True}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def get_user(self, access_token: str) -> Dict[str, Any]:
        """Récupérer les informations de l'utilisateur actuel"""
        try:
            url = f"{self.supabase_url}/auth/v1/user"
            headers = self.headers.copy()
            headers["Authorization"] = f"Bearer {access_token}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
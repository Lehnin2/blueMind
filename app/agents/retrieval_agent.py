# Agent de récupération (Retrieval Agent)
# Responsable de la recherche et de la récupération d'informations pertinentes

import os
from typing import Dict, List, Any, Optional

# Import du nouvel agent RAG
from app.agents.rag_agent import RAGAgent

class RetrievalAgent:
    """Agent responsable de la récupération d'informations réglementaires sur la pêche.
    
    Cet agent est chargé de rechercher et d'extraire les informations pertinentes
    à partir de diverses sources de données (base de données, documents, etc.)
    en fonction des requêtes des utilisateurs.
    """
    
    def __init__(self, db_connection=None, document_store=None):
        """Initialise l'agent de récupération.
        
        Args:
            db_connection: Connexion à la base de données
            document_store: Stockage de documents pour la recherche
        """
        self.db_connection = db_connection
        self.document_store = document_store
        self.search_history = []
        
        # Initialiser l'agent RAG pour la recherche sémantique
        self.rag_agent = RAGAgent()
        
        # Vérifier si l'index existe, sinon le construire
        try:
            self.rag_agent.load_index()
        except Exception as e:
            print(f"Erreur lors du chargement de l'index: {str(e)}")
            print("Construction d'un nouvel index...")
            self.rag_agent.build_index()
    
    def search_regulations(self, query, filters=None):
        """Recherche des réglementations en fonction d'une requête.
        
        Args:
            query (str): Requête de recherche
            filters (dict, optional): Filtres à appliquer (zone, espèce, etc.)
            
        Returns:
            list: Liste des réglementations correspondantes
        """
        # Utiliser l'agent RAG pour effectuer une recherche sémantique
        search_results = self.rag_agent.search(query, filters=filters)
        
        # Formater les résultats pour correspondre à l'interface attendue
        regulations = []
        for result in search_results.get("results", []):
            regulations.append({
                "title": result.get("text", "")[:50] + "...",  # Utiliser les premiers caractères comme titre
                "content": result.get("text", ""),
                "relevance": result.get("score", 0),
                "source": "Loi sur la pêche"
            })
        
        # Enregistrer la recherche dans l'historique
        self.search_history.append({"query": query, "filters": filters})
        
        return regulations
    
    def search(self, query, filters=None):
        """Recherche des informations en fonction d'une requête.
        
        Args:
            query (str): Requête de recherche
            filters (dict, optional): Filtres à appliquer (zone, espèce, etc.)
            
        Returns:
            dict: Résultats de la recherche
        """
        # Utiliser l'agent RAG pour effectuer une recherche sémantique
        results = self.rag_agent.search(query, filters=filters)
        
        # Enregistrer la recherche dans l'historique
        self.search_history.append({"query": query, "filters": filters})
        
        return results
    
    def get_species_regulations(self, species_name):
        """Récupère les réglementations spécifiques à une espèce.
        
        Args:
            species_name (str): Nom de l'espèce
            
        Returns:
            dict: Informations réglementaires sur l'espèce
        """
        # Rechercher les réglementations spécifiques à l'espèce
        query = f"réglementation pêche {species_name}"
        regulations = self.search_regulations(query, {"species": species_name})
        
        # Formater les résultats
        return {
            "species": species_name,
            "regulations": regulations,
            "fishing_periods": self._extract_fishing_periods(regulations, species_name),
            "size_limits": self._extract_size_limits(regulations, species_name),
            "quotas": self._extract_quotas(regulations, species_name)
        }
    
    def get_zone_regulations(self, zone_id):
        """Récupère les réglementations spécifiques à une zone de pêche.
        
        Args:
            zone_id (str): Identifiant de la zone
            
        Returns:
            dict: Informations réglementaires sur la zone
        """
        # Rechercher les réglementations spécifiques à la zone
        query = f"réglementation pêche zone {zone_id}"
        regulations = self.search_regulations(query, {"zone": zone_id})
        
        # Formater les résultats
        return {
            "zone": zone_id,
            "regulations": regulations,
            "restricted_areas": self._extract_restricted_areas(regulations, zone_id),
            "allowed_gear": self._extract_allowed_gear(regulations, zone_id)
        }
    
    def get_calendar_events(self, start_date=None, end_date=None, species=None, zone=None):
        """Récupère les événements du calendrier de pêche.
        
        Args:
            start_date (str, optional): Date de début
            end_date (str, optional): Date de fin
            species (str, optional): Espèce concernée
            zone (str, optional): Zone concernée
            
        Returns:
            list: Liste des événements du calendrier
        """
        # Construire la requête en fonction des paramètres
        query_parts = ["calendrier pêche"]
        if species:
            query_parts.append(species)
        if zone:
            query_parts.append(zone)
        
        query = " ".join(query_parts)
        results = self.search_regulations(query)
        
        # Logique pour extraire les événements du calendrier
        # Implémentation simplifiée
        return []
        
    def _extract_fishing_periods(self, regulations, species_name):
        """Extrait les périodes de pêche à partir des réglementations."""
        # Logique d'extraction des périodes de pêche
        # Implémentation simplifiée
        periods = []
        for reg in regulations:
            content = reg.get("content", "")
            if "période" in content.lower() and "pêche" in content.lower():
                periods.append({
                    "description": content,
                    "source": reg.get("source", "")
                })
        return periods
    
    def _extract_size_limits(self, regulations, species_name):
        """Extrait les limites de taille à partir des réglementations."""
        # Logique d'extraction des limites de taille
        # Implémentation simplifiée
        size_limits = {}
        for reg in regulations:
            content = reg.get("content", "")
            if "taille" in content.lower() and "minimale" in content.lower():
                size_limits["min_size"] = content
                size_limits["source"] = reg.get("source", "")
                break
        return size_limits
    
    def _extract_quotas(self, regulations, species_name):
        """Extrait les quotas à partir des réglementations."""
        # Logique d'extraction des quotas
        # Implémentation simplifiée
        quotas = {}
        for reg in regulations:
            content = reg.get("content", "")
            if "quota" in content.lower() or "limite" in content.lower():
                quotas["daily_limit"] = content
                quotas["source"] = reg.get("source", "")
                break
        return quotas
    
    def _extract_restricted_areas(self, regulations, zone_id):
        """Extrait les zones restreintes à partir des réglementations."""
        # Logique d'extraction des zones restreintes
        # Implémentation simplifiée
        restricted_areas = []
        for reg in regulations:
            content = reg.get("content", "")
            if "interdit" in content.lower() or "réserve" in content.lower():
                restricted_areas.append({
                    "description": content,
                    "source": reg.get("source", "")
                })
        return restricted_areas
    
    def _extract_allowed_gear(self, regulations, zone_id):
        """Extrait les engins autorisés à partir des réglementations."""
        # Logique d'extraction des engins autorisés
        # Implémentation simplifiée
        allowed_gear = []
        for reg in regulations:
            content = reg.get("content", "")
            if "engin" in content.lower() or "matériel" in content.lower():
                allowed_gear.append({
                    "description": content,
                    "source": reg.get("source", "")
                })
        return allowed_gear
    
    def get_frequent_questions(self, category=None, limit=10):
        """Récupère les questions fréquemment posées.
        
        Args:
            category (str, optional): Catégorie de questions
            limit (int, optional): Nombre maximum de questions à retourner
            
        Returns:
            list: Liste des questions fréquentes avec leurs réponses
        """
        # Construire la requête en fonction de la catégorie
        query = "questions fréquentes pêche"
        if category:
            query += f" {category}"
            
        results = self.search_regulations(query)
        
        # Limiter le nombre de résultats
        return results[:limit]
    
    def get_document_templates(self, document_type=None):
        """Récupère les modèles de documents disponibles.
        
        Args:
            document_type (str, optional): Type de document
            
        Returns:
            list: Liste des modèles de documents disponibles
        """
        # Construire la requête en fonction du type de document
        query = "modèles documents pêche"
        if document_type:
            query += f" {document_type}"
            
        results = self.search_regulations(query)
        
        # Formater les résultats
        templates = []
        for result in results:
            templates.append({
                "title": result.get("title", ""),
                "description": result.get("content", "")[:100] + "...",
                "type": document_type or "général"
            })
            
        return templates
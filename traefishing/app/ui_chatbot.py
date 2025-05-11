import json
from typing import List, Dict
from tools.groq_client import GroqClient

class UIChatbot:
    """
    Chatbot contextuel intégré via une bulle flottante présente sur toutes les pages.
    Utilise l'API Groq avec une mémoire contextuelle pour maintenir des conversations cohérentes.
    Spécialisé dans l'assistance à la navigation de l'interface utilisateur et la suggestion
    proactive de fonctionnalités pertinentes.
    """
    def __init__(self):
        self.client = GroqClient()
        self.memory = []
        self.max_memory_length = 10
        self.system_prompt = """Tu es l'assistant d'interface utilisateur de l'application GuidMarine, une application maritime pour les pêcheurs tunisiens.

Ton rôle est d'aider les utilisateurs à naviguer dans l'application et à utiliser ses fonctionnalités efficacement. Tu dois:

1. Répondre aux questions sur l'utilisation de l'interface
2. Guider les utilisateurs vers les fonctionnalités appropriées
3. Expliquer comment utiliser chaque outil disponible
4. Suggérer proactivement des fonctionnalités pertinentes selon le contexte

Fonctionnalités principales de l'application que tu dois connaître:
- Tableau de bord avec informations maritimes en temps réel
- Localisation GPS actuelle
- Calcul de profondeur à des coordonnées spécifiques
- Recherche du port le plus proche
- Planification d'itinéraires maritimes
- Affichage des cartes portuaires par gouvernorat
- Vérification des zones protégées et restrictions

Instructions:
- Adapte ton langage au niveau technique de l'utilisateur
- Comprends le français et le dialecte tunisien
- Sois concis, clair et utile
- Propose proactivement des fonctionnalités pertinentes
- Utilise un ton amical et professionnel

Historique de conversation:
{conversation_history}
"""

    def _update_memory(self, user_message: str, assistant_response: str):
        """Mettre à jour la mémoire contextuelle avec le nouvel échange"""
        self.memory.append({"user": user_message, "assistant": assistant_response})
        if len(self.memory) > self.max_memory_length:
            self.memory.pop(0)

    def _get_conversation_history(self) -> str:
        """Récupérer l'historique des conversations récentes"""
        if not self.memory:
            return "Pas de conversation antérieure."
        history = ""
        for exchange in self.memory[-3:]:  # Limité aux 3 derniers échanges pour la brièveté
            history += f"Utilisateur: {exchange['user']}\nAssistant: {exchange['assistant']}\n"
        return history.strip()

    def _detect_user_expertise(self, message: str) -> str:
        """Détecter le niveau d'expertise de l'utilisateur pour adapter les réponses"""
        technical_terms = [
            "coordonnées", "latitude", "longitude", "navigation", "bathymétrie", 
            "profondeur", "cartographie", "GPS", "waypoint", "itinéraire", "maritime"
        ]
        
        message_lower = message.lower()
        technical_term_count = sum(1 for term in technical_terms if term in message_lower)
        
        if technical_term_count >= 3:
            return "expert"
        elif technical_term_count >= 1:
            return "intermédiaire"
        else:
            return "débutant"

    def _suggest_features(self, message: str) -> str:
        """Suggérer des fonctionnalités pertinentes en fonction du message de l'utilisateur"""
        message_lower = message.lower()
        
        suggestions = ""
        
        if any(word in message_lower for word in ["où", "position", "localisation", "gps"]):
            suggestions += "\n\nVous pourriez utiliser notre fonction de localisation GPS pour voir votre position actuelle. Accédez-y depuis le menu 'Localisation'."
        
        if any(word in message_lower for word in ["profond", "profondeur", "fond", "bathymétrie"]):
            suggestions += "\n\nNotre calculateur de profondeur peut vous aider à connaître la profondeur à des coordonnées spécifiques. Vous le trouverez dans le menu 'Profondeur'."
        
        if any(word in message_lower for word in ["port", "marina", "dock", "quai"]):
            suggestions += "\n\nVous pouvez consulter les informations sur les ports tunisiens dans la section 'Ports' du menu principal."
        
        if any(word in message_lower for word in ["route", "trajet", "itinéraire", "chemin", "navigation"]):
            suggestions += "\n\nNotre planificateur d'itinéraire maritime peut vous aider à tracer votre parcours. Accédez-y depuis le menu 'Planificateur de Route'."
        
        if any(word in message_lower for word in ["protégé", "réserve", "interdit", "pêche", "restriction"]):
            suggestions += "\n\nVérifiez les zones protégées et les restrictions de pêche avec notre 'Vérificateur de Zone' accessible depuis le menu principal."
        
        return suggestions

    def handle_message(self, message: str) -> Dict[str, str]:
        """Traiter le message de l'utilisateur et générer une réponse contextuelle"""
        try:
            # Obtenir l'historique des conversations
            conversation_history = self._get_conversation_history()
            
            # Détecter le niveau d'expertise
            expertise_level = self._detect_user_expertise(message)
            
            # Préparer le prompt avec l'historique et le niveau d'expertise
            prompt = self.system_prompt.format(
                conversation_history=conversation_history
            ) + f"\n\nNiveau d'expertise détecté: {expertise_level}\n\nUtilisateur: {message}\nAssistant:"

            # Générer la réponse via l'API Groq
            response = self.client.generate_response(prompt)
            text = None
            if response and "choices" in response and response["choices"]:
                choice = response["choices"][0]
                msg = choice.get("message")
                text = msg.get("content") if msg else choice.get("text")

            if not text:
                text = "Désolé, je n'ai pas pu comprendre votre demande. Pouvez-vous préciser?"

            # Ajouter des suggestions de fonctionnalités pertinentes
            suggestions = self._suggest_features(message)
            if suggestions:
                text += suggestions

            # Mettre à jour la mémoire avec ce nouvel échange
            self._update_memory(message, text)
            return {"text": text}

        except Exception as e:
            error_msg = f"Erreur lors du traitement de la demande: {str(e)}. Veuillez réessayer."
            self._update_memory(message, error_msg)
            return {"text": error_msg}
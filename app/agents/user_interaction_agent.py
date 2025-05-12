# Agent d'interaction utilisateur (User Interaction Agent)
# Responsable de la gestion des conversations et de l'interface vocale

import requests
import json
import re

class UserInteractionAgent:
    """
    Agent responsable de l'interaction avec l'utilisateur.
    
    Cet agent est chargé de gérer les conversations avec l'utilisateur,
    de traiter les entrées vocales et textuelles, et de présenter les
    informations de manière conviviale.
    """
    
    def __init__(self, reasoning_agent=None, generation_agent=None, llm_api_key=None, llm_model="meta-llama/llama-4-scout-17b-16e-instruct"):
        """
        Initialise l'agent d'interaction utilisateur.
        
        Args:
            reasoning_agent: Agent de raisonnement pour l'analyse des requêtes
            generation_agent: Agent de génération pour les réponses
            llm_api_key: Clé API pour le modèle de langage externe (Groq)
            llm_model: Modèle de langage à utiliser
        """
        self.reasoning_agent = reasoning_agent
        self.generation_agent = generation_agent
        self.conversation_history = []
        self.llm_api_key = llm_api_key
        self.llm_model = llm_model
        self.llm_api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def process_query(self, query_text, user_profile=None, use_llm=True):
        """
        Traite une requête utilisateur et génère une réponse appropriée.
        
        Args:
            query_text (str): Texte de la requête utilisateur
            user_profile (dict, optional): Profil de l'utilisateur
            use_llm (bool): Utiliser le LLM externe pour la génération
            
        Returns:
            dict: Réponse formatée pour l'utilisateur
        """
        # Analyser la requête avec l'agent de raisonnement
        if self.reasoning_agent:
            query_analysis = self.reasoning_agent.parse_query(query_text)
        else:
            # Analyse simplifiée si l'agent de raisonnement n'est pas disponible
            query_analysis = self._simple_query_analysis(query_text)
        
        # Récupérer les données pertinentes (simulé ici)
        retrieved_data = self._mock_data_retrieval(query_analysis)
        
        # Générer la réponse
        if use_llm and self.llm_api_key:
            response = self._generate_llm_response(query_text, query_analysis, retrieved_data, user_profile)
        elif self.generation_agent:
            response = self.generation_agent.generate_response(query_analysis, retrieved_data, user_profile)
        else:
            # Réponse par défaut si aucun agent de génération n'est disponible
            response = self._default_response(query_text)
        
        # Enregistrer dans l'historique de conversation
        self.conversation_history.append({
            "query": query_text,
            "response": response,
            "timestamp": self._get_current_timestamp()
        })
        
        return response
    
    def _generate_llm_response(self, query_text, query_analysis, retrieved_data, user_profile):
        """
        Génère une réponse en utilisant l'API LLM externe (Groq).
        
        Args:
            query_text (str): Texte de la requête
            query_analysis (dict): Analyse de la requête
            retrieved_data (dict): Données récupérées
            user_profile (dict): Profil utilisateur
            
        Returns:
            dict: Réponse formatée
        """
        try:
            # Préparer le contexte pour le LLM
            context = self._prepare_llm_context(query_analysis, retrieved_data, user_profile)
            
            # Préparer les headers pour l'API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.llm_api_key}"
            }
            
            # Préparer le payload
            data = {
                "model": self.llm_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Tu es un assistant spécialisé dans la réglementation de la pêche. "
                                  "Ton objectif est de fournir des informations précises et accessibles "
                                  "aux pêcheurs sur les règles en vigueur. Utilise un langage simple et "
                                  "des explications claires. Fournis des réponses structurées avec des "
                                  "points clés quand c'est pertinent."
                    },
                    {
                        "role": "user",
                        "content": f"Contexte: {context}\n\nQuestion: {query_text}"
                    }
                ]
            }
            
            # Faire la requête à l'API
            response = requests.post(self.llm_api_url, headers=headers, data=json.dumps(data))
            
            # Vérifier si la requête a réussi
            if response.status_code == 200:
                # Extraire et formater la réponse
                llm_response = response.json()
                response_text = llm_response["choices"][0]["message"]["content"]
                
                # Structurer la réponse
                return self._structure_llm_response(response_text, query_analysis)
            else:
                # En cas d'erreur, utiliser une réponse de secours
                print(f"Erreur API LLM: {response.status_code} - {response.text}")
                return self._fallback_response(query_text)
                
        except Exception as e:
            print(f"Erreur lors de la génération LLM: {str(e)}")
            return self._fallback_response(query_text)
    
    def _prepare_llm_context(self, query_analysis, retrieved_data, user_profile):
        """
        Prépare le contexte à envoyer au LLM.
        
        Args:
            query_analysis (dict): Analyse de la requête
            retrieved_data (dict): Données récupérées
            user_profile (dict): Profil utilisateur
            
        Returns:
            str: Contexte formaté pour le LLM
        """
        context_parts = []
        
        # Ajouter les informations sur l'intention et les entités
        intent = query_analysis.get("intent", "general_query")
        context_parts.append(f"Intention détectée: {intent}")
        
        entities = query_analysis.get("entities", {})
        if entities:
            context_parts.append("Entités identifiées:")
            for entity_type, entity_values in entities.items():
                if entity_values:
                    context_parts.append(f"- {entity_type}: {', '.join(entity_values) if isinstance(entity_values, list) else entity_values}")
        
        # Ajouter les données récupérées
        if retrieved_data:
            context_parts.append("Informations disponibles:")
            for key, value in retrieved_data.items():
                if isinstance(value, str):
                    context_parts.append(f"- {key}: {value}")
                elif isinstance(value, list) and value:
                    context_parts.append(f"- {key}: {', '.join(str(item) for item in value[:3])}{'...' if len(value) > 3 else ''}")
        
        # Ajouter des informations sur le profil utilisateur si disponible
        if user_profile:
            language_pref = user_profile.get("language_preference", "standard")
            context_parts.append(f"Préférence de langage: {language_pref}")
            
            experience = user_profile.get("experience_level", "unknown")
            context_parts.append(f"Niveau d'expérience: {experience}")
        
        return "\n".join(context_parts)
    
    def _structure_llm_response(self, response_text, query_analysis):
        """
        Structure la réponse du LLM dans un format cohérent.
        
        Args:
            response_text (str): Texte de réponse du LLM
            query_analysis (dict): Analyse de la requête
            
        Returns:
            dict: Réponse structurée
        """
        # Extraire les points clés s'ils sont présents
        key_points = []
        key_points_match = re.search(r"Points clés:(.*?)(?:\n\n|$)", response_text, re.DOTALL)
        if key_points_match:
            key_points_text = key_points_match.group(1).strip()
            key_points = [point.strip().lstrip('- ') for point in key_points_text.split('\n') if point.strip()]
            # Nettoyer le texte principal
            response_text = response_text.replace(key_points_match.group(0), "").strip()
        
        # Extraire les suggestions si présentes
        suggestions = []
        suggestions_match = re.search(r"Suggestions:(.*?)(?:\n\n|$)", response_text, re.DOTALL)
        if suggestions_match:
            suggestions_text = suggestions_match.group(1).strip()
            suggestions = [suggestion.strip().lstrip('- ') for suggestion in suggestions_text.split('\n') if suggestion.strip()]
            # Nettoyer le texte principal
            response_text = response_text.replace(suggestions_match.group(0), "").strip()
        
        # Structurer la réponse en fonction de l'intention
        intent = query_analysis.get("intent", "general_query")
        
        if intent == "search_regulation":
            return {
                "text": response_text,
                "key_points": key_points,
                "sources": [],  # À remplir si disponible
                "related_topics": suggestions
            }
        elif intent == "generate_report":
            return {
                "title": self._extract_title(response_text),
                "summary": response_text,
                "sections": self._extract_sections(response_text),
                "estimated_length": 1  # Valeur par défaut
            }
        else:
            return {
                "text": response_text,
                "suggestions": suggestions or self._generate_default_suggestions(query_analysis)
            }
    
    def _extract_title(self, text):
        """
        Extrait un titre du texte de réponse.
        
        Args:
            text (str): Texte de réponse
            
        Returns:
            str: Titre extrait ou généré
        """
        title_match = re.search(r"^#\s+(.+?)\n", text)
        if title_match:
            return title_match.group(1).strip()
        
        # Si pas de titre explicite, prendre la première ligne
        first_line = text.split('\n')[0].strip()
        if len(first_line) <= 100:
            return first_line
        
        return "Rapport sur la réglementation de pêche"
    
    def _extract_sections(self, text):
        """
        Extrait des sections du texte de réponse.
        
        Args:
            text (str): Texte de réponse
            
        Returns:
            list: Sections extraites
        """
        sections = []
        section_matches = re.finditer(r"##\s+(.+?)\n(.+?)(?=\n##|$)", text, re.DOTALL)
        
        for match in section_matches:
            title = match.group(1).strip()
            content = match.group(2).strip()
            sections.append({
                "title": title,
                "preview": content[:150] + "..." if len(content) > 150 else content
            })
        
        # Si aucune section n'est trouvée, créer une section par défaut
        if not sections:
            sections.append({
                "title": "Informations générales",
                "preview": text[:150] + "..." if len(text) > 150 else text
            })
        
        return sections
    
    def _generate_default_suggestions(self, query_analysis):
        """
        Génère des suggestions par défaut basées sur l'analyse de la requête.
        
        Args:
            query_analysis (dict): Analyse de la requête
            
        Returns:
            list: Suggestions générées
        """
        suggestions = [
            "Quelles sont les périodes de pêche autorisées ?",
            "Comment obtenir un permis de pêche ?",
            "Quelles sont les sanctions en cas d'infraction ?"
        ]
        
        entities = query_analysis.get("entities", {})
        if "species" in entities and entities["species"]:
            species = entities["species"][0] if isinstance(entities["species"], list) else entities["species"]
            suggestions.append(f"Quelles techniques de pêche sont recommandées pour {species} ?")
        
        if "fishing_zones" in entities and entities["fishing_zones"]:
            zone = entities["fishing_zones"][0] if isinstance(entities["fishing_zones"], list) else entities["fishing_zones"]
            suggestions.append(f"Quelles autres espèces peut-on pêcher dans {zone} ?")
        
        return suggestions
    
    def _simple_query_analysis(self, query_text):
        """
        Analyse simplifiée d'une requête en l'absence d'agent de raisonnement.
        
        Args:
            query_text (str): Texte de la requête
            
        Returns:
            dict: Analyse simplifiée
        """
        # Logique simplifiée de détection d'intention
        intent = "general_query"
        if "rapport" in query_text.lower():
            intent = "generate_report"
        elif any(word in query_text.lower() for word in ["règlement", "loi", "autorisé", "interdit", "taille"]):
            intent = "search_regulation"
        
        # Extraction simplifiée d'entités
        entities = {
            "species": [],
            "fishing_zones": [],
            "fishing_gear": []
        }
        
        # Liste simplifiée d'espèces et de zones à détecter
        species_list = ["thon", "sardine", "dorade", "bar", "merlu", "palourde", "crevette", "poulpe"]
        zones_list = ["méditerranée", "atlantique", "manche", "golfe de gabès", "golfe du lion", "étang"]
        gear_list = ["filet", "canne", "ligne", "chalut", "casier", "harpon"]
        
        # Recherche simplifiée
        query_lower = query_text.lower()
        for species in species_list:
            if species in query_lower:
                entities["species"].append(species)
        
        for zone in zones_list:
            if zone in query_lower:
                entities["fishing_zones"].append(zone)
        
        for gear in gear_list:
            if gear in query_lower:
                entities["fishing_gear"].append(gear)
        
        return {
            "intent": intent,
            "entities": entities,
            "original_query": query_text
        }
    
    def _mock_data_retrieval(self, query_analysis):
        """
        Simule la récupération de données en l'absence d'agent de récupération.
        
        Args:
            query_analysis (dict): Analyse de la requête
            
        Returns:
            dict: Données simulées
        """
        # Données simulées pour les tests
        mock_data = {
            "content": "Les informations sur la réglementation de la pêche sont importantes pour assurer la durabilité des ressources marines.",
            "explanation": "La réglementation de la pêche vise à protéger les ressources halieutiques et à assurer une exploitation durable.",
            "sources": ["Code de l'environnement", "Arrêtés ministériels"]
        }
        
        # Ajouter des données spécifiques en fonction des entités
        entities = query_analysis.get("entities", {})
        if "species" in entities and entities["species"]:
            species = entities["species"][0] if isinstance(entities["species"], list) else entities["species"]
            mock_data["regulations"] = [
                {"title": f"Taille minimale pour {species}: 20 cm"},
                {"title": f"Période de pêche autorisée pour {species}: du 1er mars au 30 septembre"},
                {"title": f"Quota journalier pour {species}: 5 kg par pêcheur"}
            ]
        
        return mock_data
    
    def _default_response(self, query_text):
        """
        Génère une réponse par défaut en l'absence d'agent de génération.
        
        Args:
            query_text (str): Texte de la requête
            
        Returns:
            dict: Réponse par défaut
        """
        return {
            "text": "Je ne dispose pas de suffisamment d'informations pour répondre à cette question. "
                   "Veuillez préciser votre demande ou consulter la documentation officielle sur la réglementation de la pêche.",
            "suggestions": [
                "Quelle espèce de poisson vous intéresse ?",
                "Dans quelle zone souhaitez-vous pêcher ?",
                "Quel type d'information recherchez-vous (taille minimale, période, etc.) ?"
            ]
        }
    
    def _get_current_timestamp(self):
        """
        Obtient un horodatage pour l'historique des conversations.
        
        Returns:
            str: Horodatage au format ISO
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _fallback_response(self, query_text):
        """
        Génère une réponse de secours en cas d'échec du LLM.
        
        Args:
            query_text (str): Texte de la requête
            
        Returns:
            dict: Réponse de secours
        """
        return {
            "text": "Je rencontre des difficultés à traiter votre demande pour le moment. "
                   "Voici quelques informations générales qui pourraient vous être utiles.",
            "suggestions": [
                "Consultez le site officiel de la réglementation de la pêche",
                "Contactez le service des affaires maritimes local",
                "Essayez de reformuler votre question de manière plus précise"
            ]
        }
    
    def process_voice_input(self, audio_data):
        """
        Traite une entrée vocale et la convertit en texte.
        
        Args:
            audio_data: Données audio à traiter
            
        Returns:
            str: Texte transcrit
        """
        # Simuler la transcription vocale
        # Dans une implémentation réelle, utiliser un service de reconnaissance vocale
        return "Quelles sont les règles pour la pêche à la palourde ?"
    
    def generate_voice_response(self, response_text):
        """
        Génère une réponse vocale à partir d'un texte.
        
        Args:
            response_text (str): Texte à convertir en voix
            
        Returns:
            bytes: Données audio de la réponse
        """
        # Simuler la synthèse vocale
        # Dans une implémentation réelle, utiliser un service de synthèse vocale
        return b""  # Données audio simulées (vides)
    
    def get_conversation_history(self, limit=10):
        """
        Récupère l'historique des conversations.
        
        Args:
            limit (int): Nombre maximum d'échanges à récupérer
            
        Returns:
            list: Historique des conversations
        """
        return self.conversation_history[-limit:] if self.conversation_history else []
    
    def clear_conversation_history(self):
        """
        Efface l'historique des conversations.
        """
        self.conversation_history = []
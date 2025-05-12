# Agent communautaire (Community Agent)
# Responsable de la gestion des contributions des utilisateurs et de la validation des informations

from datetime import datetime

class CommunityAgent:
    """
    Agent responsable de la gestion des contributions communautaires.
    
    Cet agent est chargé de collecter, valider et intégrer les contributions
    des utilisateurs concernant la réglementation de la pêche, les observations
    de terrain et les retours d'expérience.
    """
    
    def __init__(self, reasoning_agent=None, llm_api_key=None, llm_model="meta-llama/llama-4-scout-17b-16e-instruct"):
        """
        Initialise l'agent communautaire.
        
        Args:
            reasoning_agent: Agent de raisonnement pour la validation
            llm_api_key: Clé API pour le modèle de langage externe (Groq)
            llm_model: Modèle de langage à utiliser
        """
        self.reasoning_agent = reasoning_agent
        self.llm_api_key = llm_api_key
        self.llm_model = llm_model
        self.contributions = []
        self.validation_queue = []
        self.validated_contributions = []
        self.rejected_contributions = []
    
    def submit_contribution(self, contribution_data, user_id=None):
        """
        Soumet une nouvelle contribution pour validation.
        
        Args:
            contribution_data (dict): Données de la contribution
            user_id (str, optional): Identifiant de l'utilisateur
            
        Returns:
            dict: Informations sur la contribution soumise
        """
        # Générer un identifiant unique pour la contribution
        contribution_id = f"contrib_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Préparer la structure de la contribution
        contribution = {
            "contribution_id": contribution_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "data": contribution_data,
            "status": "pending",
            "validation": None
        }
        
        # Ajouter à la liste des contributions et à la file d'attente de validation
        self.contributions.append(contribution)
        self.validation_queue.append(contribution_id)
        
        return {
            "contribution_id": contribution_id,
            "status": "submitted",
            "message": "Votre contribution a été soumise et est en attente de validation."
        }
    
    def validate_contribution(self, contribution_id, validator_id=None):
        """
        Valide une contribution en attente.
        
        Args:
            contribution_id (str): Identifiant de la contribution
            validator_id (str, optional): Identifiant du validateur
            
        Returns:
            dict: Résultat de la validation
        """
        # Rechercher la contribution
        contribution = None
        for c in self.contributions:
            if c["contribution_id"] == contribution_id:
                contribution = c
                break
        
        if not contribution:
            return {"error": "Contribution non trouvée"}
        
        if contribution["status"] != "pending":
            return {"error": f"La contribution est déjà {contribution['status']}"}
        
        # Effectuer la validation
        validation_result = self._validate_contribution_content(contribution)
        
        # Mettre à jour le statut de la contribution
        contribution["status"] = "validated" if validation_result["is_valid"] else "rejected"
        contribution["validation"] = {
            "validator_id": validator_id,
            "timestamp": datetime.now().isoformat(),
            "result": validation_result
        }
        
        # Déplacer la contribution vers la liste appropriée
        if validation_result["is_valid"]:
            self.validated_contributions.append(contribution)
        else:
            self.rejected_contributions.append(contribution)
        
        # Retirer de la file d'attente
        if contribution_id in self.validation_queue:
            self.validation_queue.remove(contribution_id)
        
        return {
            "contribution_id": contribution_id,
            "status": contribution["status"],
            "validation_result": validation_result
        }
    
    def _validate_contribution_content(self, contribution):
        """
        Valide le contenu d'une contribution.
        
        Args:
            contribution (dict): Contribution à valider
            
        Returns:
            dict: Résultat de la validation
        """
        # Utiliser l'agent de raisonnement si disponible
        if self.reasoning_agent:
            return self.reasoning_agent.validate_contribution(contribution["data"])
        else:
            # Validation simplifiée si l'agent de raisonnement n'est pas disponible
            return self._simple_validation(contribution["data"])
    
    def _simple_validation(self, contribution_data):
        """
        Effectue une validation simplifiée d'une contribution.
        
        Args:
            contribution_data (dict): Données de la contribution
            
        Returns:
            dict: Résultat de la validation
        """
        # Vérifier le type de contribution
        contribution_type = contribution_data.get("type")
        
        # Vérifications de base en fonction du type
        if contribution_type == "observation":
            return self._validate_observation(contribution_data)
        elif contribution_type == "regulation_update":
            return self._validate_regulation_update(contribution_data)
        elif contribution_type == "feedback":
            return self._validate_feedback(contribution_data)
        else:
            return {
                "is_valid": False,
                "reason": "Type de contribution non reconnu",
                "suggestions": ["Veuillez spécifier un type de contribution valide (observation, regulation_update, feedback)"]
            }
    
    def _validate_observation(self, observation_data):
        """
        Valide une observation.
        
        Args:
            observation_data (dict): Données de l'observation
            
        Returns:
            dict: Résultat de la validation
        """
        # Vérifier les champs obligatoires
        required_fields = ["location", "date", "description"]
        missing_fields = [field for field in required_fields if field not in observation_data]
        
        if missing_fields:
            return {
                "is_valid": False,
                "reason": "Champs obligatoires manquants",
                "missing_fields": missing_fields,
                "suggestions": [f"Veuillez renseigner les champs suivants : {', '.join(missing_fields)}"]
            }
        
        # Vérifier la longueur de la description
        if len(observation_data.get("description", "")) < 10:
            return {
                "is_valid": False,
                "reason": "Description trop courte",
                "suggestions": ["Veuillez fournir une description plus détaillée de votre observation"]
            }
        
        # Vérifier la date (doit être dans le passé)
        try:
            observation_date = datetime.fromisoformat(observation_data["date"])
            if observation_date > datetime.now():
                return {
                    "is_valid": False,
                    "reason": "Date invalide",
                    "suggestions": ["La date de l'observation ne peut pas être dans le futur"]
                }
        except (ValueError, TypeError):
            return {
                "is_valid": False,
                "reason": "Format de date invalide",
                "suggestions": ["Veuillez utiliser le format ISO (YYYY-MM-DD)"]
            }
        
        # Si toutes les vérifications sont passées
        return {
            "is_valid": True,
            "confidence": 0.8,  # Confiance modérée sans vérification approfondie
            "feedback": "Observation validée. Merci pour votre contribution !"
        }
    
    def _validate_regulation_update(self, update_data):
        """
        Valide une mise à jour de réglementation.
        
        Args:
            update_data (dict): Données de la mise à jour
            
        Returns:
            dict: Résultat de la validation
        """
        # Vérifier les champs obligatoires
        required_fields = ["regulation_id", "update_description", "source"]
        missing_fields = [field for field in required_fields if field not in update_data]
        
        if missing_fields:
            return {
                "is_valid": False,
                "reason": "Champs obligatoires manquants",
                "missing_fields": missing_fields,
                "suggestions": [f"Veuillez renseigner les champs suivants : {', '.join(missing_fields)}"]
            }
        
        # Vérifier la source (doit être une source officielle)
        official_sources = ["journal_officiel", "ministere", "prefecture", "site_gouvernemental"]
        if update_data.get("source_type") not in official_sources:
            return {
                "is_valid": False,
                "reason": "Source non officielle",
                "suggestions": [
                    "Les mises à jour de réglementation doivent provenir d'une source officielle",
                    f"Sources acceptées : {', '.join(official_sources)}"
                ]
            }
        
        # Vérifier l'URL de la source si fournie
        if "source_url" in update_data and not update_data["source_url"].startswith(("http://", "https://")):
            return {
                "is_valid": False,
                "reason": "URL de source invalide",
                "suggestions": ["Veuillez fournir une URL valide commençant par http:// ou https://"]
            }
        
        # Si toutes les vérifications sont passées
        return {
            "is_valid": True,
            "confidence": 0.6,  # Confiance faible sans vérification approfondie
            "feedback": "Mise à jour soumise pour vérification approfondie. Merci pour votre contribution !",
            "needs_expert_review": True  # Nécessite une revue par un expert
        }
    
    def _validate_feedback(self, feedback_data):
        """
        Valide un retour d'expérience.
        
        Args:
            feedback_data (dict): Données du retour
            
        Returns:
            dict: Résultat de la validation
        """
        # Vérifier les champs obligatoires
        required_fields = ["content", "rating"]
        missing_fields = [field for field in required_fields if field not in feedback_data]
        
        if missing_fields:
            return {
                "is_valid": False,
                "reason": "Champs obligatoires manquants",
                "missing_fields": missing_fields,
                "suggestions": [f"Veuillez renseigner les champs suivants : {', '.join(missing_fields)}"]
            }
        
        # Vérifier la note (doit être entre 1 et 5)
        rating = feedback_data.get("rating")
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return {
                    "is_valid": False,
                    "reason": "Note invalide",
                    "suggestions": ["La note doit être comprise entre 1 et 5"]
                }
        except (ValueError, TypeError):
            return {
                "is_valid": False,
                "reason": "Format de note invalide",
                "suggestions": ["La note doit être un nombre entier entre 1 et 5"]
            }
        
        # Vérifier le contenu (longueur minimale)
        if len(feedback_data.get("content", "")) < 5:
            return {
                "is_valid": False,
                "reason": "Contenu trop court",
                "suggestions": ["Veuillez fournir un retour plus détaillé"]
            }
        
        # Si toutes les vérifications sont passées
        return {
            "is_valid": True,
            "confidence": 0.9,  # Confiance élevée pour les retours
            "feedback": "Merci pour votre retour !"
        }
    
    def get_pending_contributions(self, limit=10):
        """
        Récupère les contributions en attente de validation.
        
        Args:
            limit (int): Nombre maximum de contributions à récupérer
            
        Returns:
            list: Contributions en attente
        """
        pending = []
        count = 0
        
        for contrib_id in self.validation_queue:
            if count >= limit:
                break
                
            for contribution in self.contributions:
                if contribution["contribution_id"] == contrib_id:
                    pending.append(contribution)
                    count += 1
                    break
        
        return pending
    
    def get_contribution_status(self, contribution_id):
        """
        Récupère le statut d'une contribution.
        
        Args:
            contribution_id (str): Identifiant de la contribution
            
        Returns:
            dict: Statut de la contribution
        """
        for contribution in self.contributions:
            if contribution["contribution_id"] == contribution_id:
                return {
                    "contribution_id": contribution_id,
                    "status": contribution["status"],
                    "timestamp": contribution["timestamp"],
                    "validation": contribution["validation"]
                }
        
        return {"error": "Contribution non trouvée"}
    
    def get_validated_contributions(self, limit=10, contribution_type=None):
        """
        Récupère les contributions validées.
        
        Args:
            limit (int): Nombre maximum de contributions à récupérer
            contribution_type (str, optional): Type de contribution à filtrer
            
        Returns:
            list: Contributions validées
        """
        filtered = []
        
        for contribution in self.validated_contributions:
            if contribution_type and contribution["data"].get("type") != contribution_type:
                continue
                
            filtered.append(contribution)
            
            if len(filtered) >= limit:
                break
        
        return filtered
    
    def get_contribution_statistics(self):
        """
        Récupère des statistiques sur les contributions.
        
        Returns:
            dict: Statistiques sur les contributions
        """
        # Compter les contributions par type et par statut
        type_counts = {}
        status_counts = {
            "pending": len(self.validation_queue),
            "validated": len(self.validated_contributions),
            "rejected": len(self.rejected_contributions)
        }
        
        # Compter par type
        for contribution in self.contributions:
            contrib_type = contribution["data"].get("type")
            if contrib_type:
                if contrib_type not in type_counts:
                    type_counts[contrib_type] = 0
                type_counts[contrib_type] += 1
        
        return {
            "total": len(self.contributions),
            "by_status": status_counts,
            "by_type": type_counts
        }
    
    def search_contributions(self, search_query, filters=None):
        """
        Recherche des contributions selon des critères.
        
        Args:
            search_query (str): Texte à rechercher
            filters (dict, optional): Filtres à appliquer
            
        Returns:
            list: Contributions correspondantes
        """
        results = []
        search_query = search_query.lower()
        
        for contribution in self.contributions:
            # Appliquer les filtres si spécifiés
            if filters:
                if "status" in filters and contribution["status"] != filters["status"]:
                    continue
                    
                if "type" in filters and contribution["data"].get("type") != filters["type"]:
                    continue
                    
                if "user_id" in filters and contribution["user_id"] != filters["user_id"]:
                    continue
            
            # Rechercher dans le contenu
            match_found = False
            
            # Rechercher dans la description pour les observations
            if contribution["data"].get("type") == "observation" and "description" in contribution["data"]:
                if search_query in contribution["data"]["description"].lower():
                    match_found = True
            
            # Rechercher dans la description de mise à jour pour les mises à jour de réglementation
            elif contribution["data"].get("type") == "regulation_update" and "update_description" in contribution["data"]:
                if search_query in contribution["data"]["update_description"].lower():
                    match_found = True
            
            # Rechercher dans le contenu pour les retours
            elif contribution["data"].get("type") == "feedback" and "content" in contribution["data"]:
                if search_query in contribution["data"]["content"].lower():
                    match_found = True
            
            if match_found:
                results.append(contribution)
        
        return results
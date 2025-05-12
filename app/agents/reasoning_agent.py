# Agent de raisonnement (Reasoning Agent)
# Responsable de l'analyse des requêtes, de la définition du périmètre des rapports et de la validation des contributions

class ReasoningAgent:
    """
    Agent responsable du raisonnement et de l'analyse des requêtes utilisateur.
    
    Cet agent est chargé d'analyser les requêtes des utilisateurs, de déterminer
    le périmètre des rapports à générer et de valider les contributions communautaires.
    """
    
    def __init__(self):
        """
        Initialise l'agent de raisonnement.
        """
        self.query_history = []
        self.validation_history = []
    
    def parse_query(self, query_text):
        """
        Analyse une requête utilisateur pour en extraire les intentions et entités.
        
        Args:
            query_text (str): Texte de la requête utilisateur
            
        Returns:
            dict: Structure contenant l'intention et les entités identifiées
        """
        # Logique d'analyse de la requête
        # À implémenter avec NLP ou règles spécifiques
        intent = self._detect_intent(query_text)
        entities = self._extract_entities(query_text)
        
        # Enregistrer dans l'historique
        self.query_history.append({"query": query_text, "intent": intent, "entities": entities})
        
        return {
            "intent": intent,
            "entities": entities,
            "original_query": query_text
        }
    
    def _detect_intent(self, query_text):
        """
        Détecte l'intention principale de la requête.
        
        Args:
            query_text (str): Texte de la requête
            
        Returns:
            str: Intention identifiée
        """
        # Logique de détection d'intention
        # Exemple simplifié
        if "rapport" in query_text.lower():
            return "generate_report"
        elif "règlement" in query_text.lower() or "loi" in query_text.lower():
            return "search_regulation"
        elif "quiz" in query_text.lower() or "test" in query_text.lower():
            return "start_quiz"
        elif "contribuer" in query_text.lower() or "observation" in query_text.lower():
            return "contribute"
        else:
            return "general_query"
    
    def _extract_entities(self, query_text):
        """
        Extrait les entités pertinentes de la requête.
        
        Args:
            query_text (str): Texte de la requête
            
        Returns:
            dict: Entités extraites (espèces, zones, engins, etc.)
        """
        # Logique d'extraction d'entités
        # À implémenter avec NLP ou règles spécifiques
        entities = {
            "species": [],
            "fishing_zones": [],
            "fishing_gear": [],
            "time_period": None
        }
        
        # Exemple simplifié d'extraction
        if "palourde" in query_text.lower():
            entities["species"].append("palourde")
        if "golfe de gabès" in query_text.lower():
            entities["fishing_zones"].append("golfe_de_gabes")
        if "filet" in query_text.lower():
            entities["fishing_gear"].append("filet")
        
        return entities
    
    def scope_report(self, query_analysis, available_data):
        """
        Définit le périmètre d'un rapport à générer.
        
        Args:
            query_analysis (dict): Analyse de la requête utilisateur
            available_data (dict): Données disponibles pour le rapport
            
        Returns:
            dict: Structure du rapport à générer
        """
        # Logique de définition du périmètre du rapport
        report_structure = {
            "title": self._generate_report_title(query_analysis),
            "sections": self._determine_report_sections(query_analysis, available_data),
            "data_requirements": self._identify_data_needs(query_analysis)
        }
        
        return report_structure
    
    def _generate_report_title(self, query_analysis):
        """
        Génère un titre approprié pour le rapport.
        
        Args:
            query_analysis (dict): Analyse de la requête
            
        Returns:
            str: Titre du rapport
        """
        # Logique de génération de titre
        entities = query_analysis.get("entities", {})
        species = ", ".join(entities.get("species", ["pêche"]))
        zones = ", ".join(entities.get("fishing_zones", []))
        
        if zones:
            return f"Réglementation de la pêche de {species} dans {zones}"
        else:
            return f"Réglementation concernant la pêche de {species}"
    
    def _determine_report_sections(self, query_analysis, available_data):
        """
        Détermine les sections à inclure dans le rapport.
        
        Args:
            query_analysis (dict): Analyse de la requête
            available_data (dict): Données disponibles
            
        Returns:
            list: Sections du rapport
        """
        # Logique de détermination des sections
        sections = ["Introduction"]
        
        # Ajouter des sections en fonction des entités identifiées
        entities = query_analysis.get("entities", {})
        if entities.get("species"):
            sections.append("Espèces concernées")
        if entities.get("fishing_zones"):
            sections.append("Zones de pêche")
        if entities.get("fishing_gear"):
            sections.append("Engins de pêche autorisés")
        
        # Toujours inclure ces sections
        sections.extend(["Périodes de pêche", "Sanctions applicables", "Références légales"])
        
        return sections
    
    def _identify_data_needs(self, query_analysis):
        """
        Identifie les données nécessaires pour le rapport.
        
        Args:
            query_analysis (dict): Analyse de la requête
            
        Returns:
            dict: Besoins en données
        """
        # Logique d'identification des besoins en données
        return {
            "regulations": True,
            "maps": "fishing_zones" in query_analysis.get("entities", {}),
            "species_info": bool(query_analysis.get("entities", {}).get("species")),
            "historical_data": False
        }
    
    def validate_contribution(self, contribution_data):
        """
        Valide une contribution communautaire.
        
        Args:
            contribution_data (dict): Données de la contribution
            
        Returns:
            dict: Résultat de la validation avec score et commentaires
        """
        # Logique de validation des contributions
        validation_result = {
            "is_valid": self._check_contribution_validity(contribution_data),
            "confidence_score": self._calculate_confidence_score(contribution_data),
            "feedback": self._generate_validation_feedback(contribution_data),
            "needs_expert_review": self._needs_expert_review(contribution_data)
        }
        
        # Enregistrer dans l'historique de validation
        self.validation_history.append({
            "contribution": contribution_data,
            "validation": validation_result
        })
        
        return validation_result
    
    def _check_contribution_validity(self, contribution_data):
        """
        Vérifie si une contribution est valide.
        
        Args:
            contribution_data (dict): Données de la contribution
            
        Returns:
            bool: True si la contribution est valide
        """
        # Logique de vérification de validité
        # Vérifier les champs obligatoires
        required_fields = ["location", "date", "description"]
        for field in required_fields:
            if field not in contribution_data or not contribution_data[field]:
                return False
        
        return True
    
    def _calculate_confidence_score(self, contribution_data):
        """
        Calcule un score de confiance pour la contribution.
        
        Args:
            contribution_data (dict): Données de la contribution
            
        Returns:
            float: Score de confiance entre 0 et 1
        """
        # Logique de calcul du score de confiance
        # Exemple simplifié
        score = 0.5  # Score de base
        
        # Bonus pour les champs détaillés
        if "photo" in contribution_data and contribution_data["photo"]:
            score += 0.2
        if len(contribution_data.get("description", "")) > 100:
            score += 0.1
        if "contact_info" in contribution_data and contribution_data["contact_info"]:
            score += 0.1
        
        # Limiter à 1.0
        return min(score, 1.0)
    
    def _generate_validation_feedback(self, contribution_data):
        """
        Génère un feedback pour la contribution.
        
        Args:
            contribution_data (dict): Données de la contribution
            
        Returns:
            str: Feedback pour l'utilisateur
        """
        # Logique de génération de feedback
        if not self._check_contribution_validity(contribution_data):
            return "Contribution incomplète. Veuillez remplir tous les champs obligatoires."
        
        score = self._calculate_confidence_score(contribution_data)
        if score > 0.8:
            return "Excellente contribution! Merci pour ces informations détaillées."
        elif score > 0.6:
            return "Bonne contribution. Vous pourriez ajouter une photo pour l'améliorer."
        else:
            return "Contribution reçue. Merci d'ajouter plus de détails pour faciliter sa validation."
    
    def _needs_expert_review(self, contribution_data):
        """
        Détermine si la contribution nécessite une revue par un expert.
        
        Args:
            contribution_data (dict): Données de la contribution
            
        Returns:
            bool: True si une revue d'expert est nécessaire
        """
        # Logique pour déterminer si une revue d'expert est nécessaire
        # Exemple: les contributions avec des mots-clés sensibles nécessitent une revue
        sensitive_keywords = ["illégal", "braconnage", "pollution", "mort"]
        description = contribution_data.get("description", "").lower()
        
        for keyword in sensitive_keywords:
            if keyword in description:
                return True
        
        # Les contributions avec un faible score de confiance nécessitent une revue
        if self._calculate_confidence_score(contribution_data) < 0.4:
            return True
        
        return False
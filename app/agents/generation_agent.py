# Agent de génération (Generation Agent)
# Responsable de la production de réponses adaptées aux pêcheurs et de retours pour les quiz

class GenerationAgent:
    """
    Agent responsable de la génération de contenu adapté aux pêcheurs.
    
    Cet agent est chargé de produire des réponses dans un langage accessible
    aux pêcheurs et de fournir des retours pédagogiques pour les quiz.
    """
    
    def __init__(self, language_model=None):
        """
        Initialise l'agent de génération.
        
        Args:
            language_model: Modèle de langage à utiliser pour la génération
        """
        self.language_model = language_model
        self.generation_history = []
    
    def generate_response(self, query_analysis, retrieved_data, user_profile=None):
        """
        Génère une réponse adaptée à l'utilisateur à partir des données récupérées.
        
        Args:
            query_analysis (dict): Analyse de la requête utilisateur
            retrieved_data (dict): Données récupérées par l'agent de récupération
            user_profile (dict, optional): Profil de l'utilisateur pour personnalisation
            
        Returns:
            dict: Réponse générée avec différents formats (texte, points clés, etc.)
        """
        # Logique de génération de réponse
        intent = query_analysis.get("intent", "general_query")
        entities = query_analysis.get("entities", {})
        
        # Adapter le style en fonction du profil utilisateur
        language_level = "simple" if user_profile and user_profile.get("language_preference") == "simple" else "standard"
        
        # Générer la réponse en fonction de l'intention
        if intent == "search_regulation":
            response = self._generate_regulation_response(retrieved_data, entities, language_level)
        elif intent == "generate_report":
            response = self._generate_report_preview(retrieved_data, entities, language_level)
        else:
            response = self._generate_general_response(retrieved_data, query_analysis, language_level)
        
        # Enregistrer dans l'historique
        self.generation_history.append({
            "query_analysis": query_analysis,
            "response": response
        })
        
        return response
    
    def _generate_regulation_response(self, retrieved_data, entities, language_level):
        """
        Génère une réponse concernant la réglementation.
        
        Args:
            retrieved_data (dict): Données récupérées
            entities (dict): Entités identifiées dans la requête
            language_level (str): Niveau de langage à utiliser
            
        Returns:
            dict: Réponse formatée
        """
        # Logique de génération pour les réglementations
        # Adapter le langage en fonction du niveau demandé
        if language_level == "simple":
            explanation = self._simplify_text(retrieved_data.get("explanation", ""))
            key_points = self._extract_and_simplify_key_points(retrieved_data)
        else:
            explanation = retrieved_data.get("explanation", "")
            key_points = self._extract_key_points(retrieved_data)
        
        return {
            "text": explanation,
            "key_points": key_points,
            "sources": retrieved_data.get("sources", []),
            "related_topics": self._suggest_related_topics(entities)
        }
    
    def _generate_report_preview(self, retrieved_data, entities, language_level):
        """
        Génère un aperçu de rapport.
        
        Args:
            retrieved_data (dict): Données récupérées
            entities (dict): Entités identifiées dans la requête
            language_level (str): Niveau de langage à utiliser
            
        Returns:
            dict: Aperçu du rapport
        """
        # Logique de génération d'aperçu de rapport
        return {
            "title": self._generate_title(entities),
            "summary": self._generate_summary(retrieved_data, language_level),
            "sections": self._generate_section_previews(retrieved_data, language_level),
            "estimated_length": self._estimate_report_length(retrieved_data)
        }
    
    def _generate_general_response(self, retrieved_data, query_analysis, language_level):
        """
        Génère une réponse générale.
        
        Args:
            retrieved_data (dict): Données récupérées
            query_analysis (dict): Analyse de la requête
            language_level (str): Niveau de langage à utiliser
            
        Returns:
            dict: Réponse générale formatée
        """
        # Logique de génération pour les requêtes générales
        original_query = query_analysis.get("original_query", "")
        
        if language_level == "simple":
            response_text = self._simplify_text(retrieved_data.get("content", ""))
        else:
            response_text = retrieved_data.get("content", "")
        
        return {
            "text": response_text,
            "suggestions": self._generate_follow_up_suggestions(original_query, retrieved_data)
        }
    
    def _simplify_text(self, text):
        """
        Simplifie un texte pour le rendre plus accessible.
        
        Args:
            text (str): Texte à simplifier
            
        Returns:
            str: Texte simplifié
        """
        # Logique de simplification de texte
        # Exemple simplifié
        simplified = text
        
        # Remplacer les termes techniques par des équivalents plus simples
        technical_terms = {
            "dispositif": "outil",
            "embarcation": "bateau",
            "spécimen": "poisson",
            "législation": "règles",
            "procéder à": "faire",
            "en vigueur": "actuel"
        }
        
        for term, replacement in technical_terms.items():
            simplified = simplified.replace(term, replacement)
        
        return simplified
    
    def _extract_key_points(self, data):
        """
        Extrait les points clés des données.
        
        Args:
            data (dict): Données à analyser
            
        Returns:
            list: Points clés extraits
        """
        # Logique d'extraction de points clés
        # Exemple simplifié
        key_points = []
        
        if "regulations" in data:
            for reg in data["regulations"][:5]:  # Limiter à 5 points
                key_points.append(reg.get("title", ""))
        
        return key_points
    
    def _extract_and_simplify_key_points(self, data):
        """
        Extrait et simplifie les points clés.
        
        Args:
            data (dict): Données à analyser
            
        Returns:
            list: Points clés simplifiés
        """
        # Extraire puis simplifier
        key_points = self._extract_key_points(data)
        return [self._simplify_text(point) for point in key_points]
    
    def _suggest_related_topics(self, entities):
        """
        Suggère des sujets connexes basés sur les entités.
        
        Args:
            entities (dict): Entités identifiées
            
        Returns:
            list: Sujets connexes suggérés
        """
        # Logique de suggestion de sujets connexes
        related = []
        
        if "species" in entities and entities["species"]:
            related.append(f"Techniques de pêche pour {', '.join(entities['species'])}")
        
        if "fishing_zones" in entities and entities["fishing_zones"]:
            related.append(f"Autres espèces présentes dans {', '.join(entities['fishing_zones'])}")
        
        # Toujours suggérer ces sujets généraux
        related.extend(["Périodes de pêche autorisées", "Sanctions en cas d'infraction"])
        
        return related
    
    def _generate_title(self, entities):
        """
        Génère un titre basé sur les entités.
        
        Args:
            entities (dict): Entités identifiées
            
        Returns:
            str: Titre généré
        """
        # Logique de génération de titre
        species = ", ".join(entities.get("species", ["poissons"]))
        zones = ", ".join(entities.get("fishing_zones", []))
        
        if zones:
            return f"Réglementation de la pêche de {species} dans {zones}"
        else:
            return f"Réglementation concernant la pêche de {species}"
    
    def _generate_summary(self, data, language_level):
        """
        Génère un résumé des données.
        
        Args:
            data (dict): Données à résumer
            language_level (str): Niveau de langage
            
        Returns:
            str: Résumé généré
        """
        # Logique de génération de résumé
        summary = data.get("summary", "Aucun résumé disponible.")
        
        if language_level == "simple":
            return self._simplify_text(summary)
        return summary
    
    def _generate_section_previews(self, data, language_level):
        """
        Génère des aperçus de sections pour un rapport.
        
        Args:
            data (dict): Données pour les sections
            language_level (str): Niveau de langage
            
        Returns:
            list: Aperçus des sections
        """
        # Logique de génération d'aperçus de sections
        sections = []
        
        if "sections" in data:
            for section in data["sections"]:
                preview = section.get("preview", "")
                if language_level == "simple":
                    preview = self._simplify_text(preview)
                
                sections.append({
                    "title": section.get("title", ""),
                    "preview": preview
                })
        
        return sections
    
    def _estimate_report_length(self, data):
        """
        Estime la longueur d'un rapport.
        
        Args:
            data (dict): Données du rapport
            
        Returns:
            int: Nombre estimé de pages
        """
        # Logique d'estimation de longueur
        # Exemple simplifié
        section_count = len(data.get("sections", []))
        return max(1, section_count // 2)  # Au moins 1 page, environ 2 sections par page
    
    def _generate_follow_up_suggestions(self, query, data):
        """
        Génère des suggestions de questions de suivi.
        
        Args:
            query (str): Requête originale
            data (dict): Données récupérées
            
        Returns:
            list: Suggestions de questions de suivi
        """
        # Logique de génération de suggestions de suivi
        suggestions = [
            "Quelles sont les sanctions en cas d'infraction ?",
            "Où puis-je trouver le texte complet de la réglementation ?"
        ]
        
        # Ajouter des suggestions spécifiques en fonction de la requête
        if "taille" in query.lower() or "dimension" in query.lower():
            suggestions.append("Quels sont les outils pour mesurer correctement les prises ?")
        
        if "zone" in query.lower() or "région" in query.lower():
            suggestions.append("Y a-t-il une carte des zones de pêche autorisées ?")
        
        return suggestions
    
    def generate_quiz_feedback(self, quiz_response, correct_answer, explanation=None):
        """
        Génère un retour pédagogique pour une réponse de quiz.
        
        Args:
            quiz_response (str): Réponse de l'utilisateur au quiz
            correct_answer (str): Réponse correcte
            explanation (str, optional): Explication supplémentaire
            
        Returns:
            dict: Retour formaté pour la réponse au quiz
        """
        # Logique de génération de retour pour les quiz
        is_correct = quiz_response.lower() == correct_answer.lower()
        
        if is_correct:
            feedback_text = "Bravo ! Votre réponse est correcte."
        else:
            feedback_text = f"Ce n'est pas tout à fait ça. La réponse correcte est : {correct_answer}."
        
        if explanation:
            feedback_text += f"\n\n{explanation}"
        
        # Ajouter des conseils supplémentaires
        tips = self._generate_learning_tips(quiz_response, correct_answer)
        
        return {
            "is_correct": is_correct,
            "feedback_text": feedback_text,
            "explanation": explanation,
            "learning_tips": tips
        }
    
    def _generate_learning_tips(self, user_response, correct_answer):
        """
        Génère des conseils d'apprentissage basés sur la réponse de l'utilisateur.
        
        Args:
            user_response (str): Réponse de l'utilisateur
            correct_answer (str): Réponse correcte
            
        Returns:
            list: Conseils d'apprentissage
        """
        # Logique de génération de conseils d'apprentissage
        # Exemple simplifié
        tips = [
            "Consultez régulièrement la réglementation, elle peut changer.",
            "En cas de doute, il est toujours préférable de vérifier avant de pêcher."
        ]
        
        return tips
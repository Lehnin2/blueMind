# Agent de génération de rapports (Report Generation Agent)
# Responsable de la création de rapports PDF sur la réglementation

import json
import os
from datetime import datetime

class ReportGenerationAgent:
    """
    Agent responsable de la génération de rapports sur la réglementation de la pêche.
    
    Cet agent est chargé de créer des rapports structurés et formatés (PDF)
    à partir des informations réglementaires récupérées.
    """
    
    def __init__(self, retrieval_agent=None, generation_agent=None, llm_api_key=None, llm_model="meta-llama/llama-4-scout-17b-16e-instruct"):
        """
        Initialise l'agent de génération de rapports.
        
        Args:
            retrieval_agent: Agent de récupération pour obtenir les données
            generation_agent: Agent de génération pour le contenu textuel
            llm_api_key: Clé API pour le modèle de langage externe (Groq)
            llm_model: Modèle de langage à utiliser
        """
        self.retrieval_agent = retrieval_agent
        self.generation_agent = generation_agent
        self.llm_api_key = llm_api_key
        self.llm_model = llm_model
        self.report_history = []
        self.templates = self._load_default_templates()
    
    def _load_default_templates(self):
        """
        Charge les modèles de rapport par défaut.
        
        Returns:
            dict: Modèles de rapport disponibles
        """
        # Modèles par défaut (dans une implémentation réelle, ils seraient chargés depuis des fichiers)
        return {
            "standard": {
                "sections": [
                    "Introduction",
                    "Cadre réglementaire",
                    "Espèces concernées",
                    "Zones de pêche",
                    "Périodes autorisées",
                    "Techniques et équipements",
                    "Sanctions et contrôles",
                    "Ressources complémentaires"
                ],
                "style": {
                    "font": "Arial",
                    "title_size": 16,
                    "heading_size": 14,
                    "body_size": 11,
                    "line_spacing": 1.2
                }
            },
            "simplified": {
                "sections": [
                    "Ce qu'il faut savoir",
                    "Règles principales",
                    "Calendrier de pêche",
                    "Contacts utiles"
                ],
                "style": {
                    "font": "Arial",
                    "title_size": 18,
                    "heading_size": 16,
                    "body_size": 12,
                    "line_spacing": 1.5
                }
            }
        }
    
    def generate_report(self, report_request, user_profile=None):
        """
        Génère un rapport complet sur la réglementation.
        
        Args:
            report_request (dict): Paramètres du rapport demandé
            user_profile (dict, optional): Profil de l'utilisateur
            
        Returns:
            dict: Informations sur le rapport généré
        """
        # Extraire les paramètres du rapport
        report_type = report_request.get("type", "standard")
        species = report_request.get("species", [])
        zones = report_request.get("zones", [])
        include_sections = report_request.get("sections", [])
        
        # Récupérer les données nécessaires
        report_data = self._gather_report_data(species, zones)
        
        # Générer le contenu du rapport
        report_content = self._generate_report_content(report_data, report_type, include_sections, user_profile)
        
        # Créer le rapport (simulé ici)
        report_info = self._create_report_file(report_content, report_type)
        
        # Enregistrer dans l'historique
        self.report_history.append({
            "report_id": report_info["report_id"],
            "timestamp": datetime.now().isoformat(),
            "parameters": report_request,
            "status": "generated"
        })
        
        return report_info
    
    def _gather_report_data(self, species, zones):
        """
        Rassemble les données nécessaires pour le rapport.
        
        Args:
            species (list): Liste des espèces concernées
            zones (list): Liste des zones concernées
            
        Returns:
            dict: Données pour le rapport
        """
        report_data = {
            "regulations": [],
            "species_info": {},
            "zone_info": {},
            "calendar": []
        }
        
        # Utiliser l'agent de récupération si disponible
        if self.retrieval_agent:
            # Récupérer les réglementations générales
            regulations = self.retrieval_agent.search_regulations(
                "réglementation générale",
                {"species": species, "zones": zones}
            )
            report_data["regulations"] = regulations
            
            # Récupérer les informations spécifiques aux espèces
            for species_name in species:
                species_info = self.retrieval_agent.get_species_regulations(species_name)
                if species_info:
                    report_data["species_info"][species_name] = species_info
            
            # Récupérer les informations spécifiques aux zones
            for zone_id in zones:
                zone_info = self.retrieval_agent.get_zone_regulations(zone_id)
                if zone_info:
                    report_data["zone_info"][zone_id] = zone_info
            
            # Récupérer le calendrier
            calendar = self.retrieval_agent.get_calendar_events(
                start_date=datetime.now().strftime("%Y-%m-%d"),
                end_date=None,  # Pas de date de fin (tous les événements futurs)
                species=species,
                zone=zones[0] if zones else None
            )
            report_data["calendar"] = calendar
        else:
            # Données simulées si l'agent de récupération n'est pas disponible
            report_data = self._mock_report_data(species, zones)
        
        return report_data
    
    def _mock_report_data(self, species, zones):
        """
        Génère des données simulées pour le rapport.
        
        Args:
            species (list): Liste des espèces concernées
            zones (list): Liste des zones concernées
            
        Returns:
            dict: Données simulées
        """
        mock_data = {
            "regulations": [
                {"title": "Obligation de détenir un permis de pêche", "content": "Tout pêcheur doit être en possession d'un permis de pêche valide."},
                {"title": "Respect des tailles minimales", "content": "Les spécimens pêchés doivent respecter les tailles minimales réglementaires."},
                {"title": "Respect des quotas", "content": "Les quotas journaliers et annuels doivent être strictement respectés."},
            ],
            "species_info": {},
            "zone_info": {},
            "calendar": [
                {"date": "2023-06-01", "event": "Ouverture de la pêche estivale", "description": "Début de la saison de pêche estivale dans toutes les zones."},
                {"date": "2023-09-30", "event": "Fermeture de la pêche estivale", "description": "Fin de la saison de pêche estivale dans toutes les zones."},
            ]
        }
        
        # Ajouter des informations spécifiques aux espèces
        for species_name in species:
            mock_data["species_info"][species_name] = {
                "scientific_name": f"Scientificus {species_name}",
                "min_size": "20 cm",
                "quota": "5 kg par jour",
                "protected_period": "du 1er novembre au 28 février",
                "authorized_techniques": ["Ligne", "Filet", "Casier"]
            }
        
        # Ajouter des informations spécifiques aux zones
        for zone_id in zones:
            mock_data["zone_info"][zone_id] = {
                "name": f"Zone de {zone_id}",
                "coordinates": "Coordonnées GPS",
                "specific_rules": ["Interdiction de pêche de nuit", "Respect des zones protégées"],
                "authorized_periods": "Du lever au coucher du soleil"
            }
        
        return mock_data
    
    def _generate_report_content(self, report_data, report_type, include_sections, user_profile):
        """
        Génère le contenu textuel du rapport.
        
        Args:
            report_data (dict): Données pour le rapport
            report_type (str): Type de rapport (standard, simplified, etc.)
            include_sections (list): Sections à inclure
            user_profile (dict): Profil de l'utilisateur
            
        Returns:
            dict: Contenu structuré du rapport
        """
        # Sélectionner le modèle approprié
        template = self.templates.get(report_type, self.templates["standard"])
        
        # Déterminer les sections à inclure
        if not include_sections:
            include_sections = template["sections"]
        
        # Préparer la structure du contenu
        content = {
            "title": self._generate_report_title(report_data),
            "date": datetime.now().strftime("%d/%m/%Y"),
            "sections": []
        }
        
        # Générer le contenu pour chaque section
        for section_name in include_sections:
            if section_name in template["sections"]:
                section_content = self._generate_section_content(section_name, report_data, user_profile)
                content["sections"].append({
                    "title": section_name,
                    "content": section_content
                })
        
        return content
    
    def _generate_report_title(self, report_data):
        """
        Génère un titre pour le rapport.
        
        Args:
            report_data (dict): Données du rapport
            
        Returns:
            str: Titre du rapport
        """
        # Extraire les espèces et zones pour le titre
        species_names = list(report_data["species_info"].keys())
        zone_names = list(report_data["zone_info"].keys())
        
        if species_names and zone_names:
            species_str = ", ".join(species_names)
            zone_str = ", ".join(zone_names)
            return f"Réglementation de la pêche de {species_str} dans {zone_str}"
        elif species_names:
            species_str = ", ".join(species_names)
            return f"Réglementation de la pêche de {species_str}"
        elif zone_names:
            zone_str = ", ".join(zone_names)
            return f"Réglementation de la pêche dans {zone_str}"
        else:
            return "Réglementation générale de la pêche"
    
    def _generate_section_content(self, section_name, report_data, user_profile):
        """
        Génère le contenu d'une section spécifique.
        
        Args:
            section_name (str): Nom de la section
            report_data (dict): Données du rapport
            user_profile (dict): Profil de l'utilisateur
            
        Returns:
            str: Contenu de la section
        """
        # Utiliser l'agent de génération si disponible
        if self.generation_agent:
            # Préparer une analyse de requête simulée
            query_analysis = {
                "intent": "generate_report",
                "entities": {
                    "species": list(report_data["species_info"].keys()),
                    "fishing_zones": list(report_data["zone_info"].keys())
                },
                "section": section_name
            }
            
            # Générer le contenu avec l'agent de génération
            section_data = {
                "section_name": section_name,
                "report_data": report_data
            }
            
            response = self.generation_agent.generate_response(query_analysis, section_data, user_profile)
            return response.get("text", "")
        else:
            # Générer un contenu par défaut en fonction du nom de la section
            return self._generate_default_section_content(section_name, report_data)
    
    def _generate_default_section_content(self, section_name, report_data):
        """
        Génère un contenu par défaut pour une section.
        
        Args:
            section_name (str): Nom de la section
            report_data (dict): Données du rapport
            
        Returns:
            str: Contenu par défaut
        """
        # Contenu par défaut en fonction du nom de la section
        if section_name == "Introduction" or section_name == "Ce qu'il faut savoir":
            return "Ce rapport présente les principales réglementations en vigueur concernant la pêche. Il est important de respecter ces règles pour préserver les ressources halieutiques et éviter les sanctions."
        
        elif section_name == "Cadre réglementaire" or section_name == "Règles principales":
            regulations = report_data.get("regulations", [])
            content = "La pêche est encadrée par plusieurs textes réglementaires qui visent à assurer la durabilité des ressources.\n\n"
            
            for reg in regulations:
                content += f"- {reg.get('title', '')}: {reg.get('content', '')}\n"
            
            return content
        
        elif section_name == "Espèces concernées":
            species_info = report_data.get("species_info", {})
            content = "Voici les informations spécifiques aux espèces concernées par ce rapport:\n\n"
            
            for species_name, info in species_info.items():
                content += f"### {species_name.capitalize()}\n"
                content += f"- Nom scientifique: {info.get('scientific_name', 'Non spécifié')}\n"
                content += f"- Taille minimale: {info.get('min_size', 'Non spécifiée')}\n"
                content += f"- Quota: {info.get('quota', 'Non spécifié')}\n"
                content += f"- Période protégée: {info.get('protected_period', 'Non spécifiée')}\n"
                content += f"- Techniques autorisées: {', '.join(info.get('authorized_techniques', ['Non spécifiées']))}\n\n"
            
            return content
        
        elif section_name == "Zones de pêche":
            zone_info = report_data.get("zone_info", {})
            content = "Voici les informations spécifiques aux zones de pêche concernées par ce rapport:\n\n"
            
            for zone_id, info in zone_info.items():
                content += f"### {info.get('name', zone_id)}\n"
                content += f"- Coordonnées: {info.get('coordinates', 'Non spécifiées')}\n"
                content += f"- Règles spécifiques:\n"
                for rule in info.get("specific_rules", ["Aucune règle spécifique"]):
                    content += f"  * {rule}\n"
                content += f"- Périodes autorisées: {info.get('authorized_periods', 'Non spécifiées')}\n\n"
            
            return content
        
        elif section_name == "Périodes autorisées" or section_name == "Calendrier de pêche":
            calendar = report_data.get("calendar", [])
            content = "Voici le calendrier des périodes de pêche:\n\n"
            
            for event in calendar:
                content += f"- {event.get('date', '')}: {event.get('event', '')}\n"
                if "description" in event:
                    content += f"  {event['description']}\n"
            
            return content
        
        elif section_name == "Techniques et équipements":
            return "Les techniques et équipements de pêche doivent être conformes à la réglementation. Certains équipements peuvent être interdits dans certaines zones ou pour certaines espèces."
        
        elif section_name == "Sanctions et contrôles":
            return "Le non-respect de la réglementation peut entraîner des sanctions administratives et pénales, allant de l'amende à la confiscation du matériel, voire à des peines d'emprisonnement pour les infractions les plus graves."
        
        elif section_name == "Ressources complémentaires" or section_name == "Contacts utiles":
            return "Pour plus d'informations, vous pouvez consulter les sites officiels des autorités de pêche ou contacter les services locaux des affaires maritimes."
        
        else:
            return "Informations non disponibles pour cette section."
    
    def _create_report_file(self, report_content, report_type):
        """
        Crée un fichier de rapport (simulé).
        
        Args:
            report_content (dict): Contenu du rapport
            report_type (str): Type de rapport
            
        Returns:
            dict: Informations sur le rapport créé
        """
        # Générer un identifiant unique pour le rapport
        report_id = f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Dans une implémentation réelle, on générerait un PDF ici
        # Pour cette simulation, on enregistre simplement le contenu en JSON
        report_filename = f"{report_id}.json"
        
        # Simuler l'enregistrement du fichier
        # report_path = os.path.join("reports", report_filename)
        # with open(report_path, "w", encoding="utf-8") as f:
        #     json.dump(report_content, f, ensure_ascii=False, indent=2)
        
        return {
            "report_id": report_id,
            "title": report_content["title"],
            "date": report_content["date"],
            "type": report_type,
            "filename": report_filename,
            "sections": [section["title"] for section in report_content["sections"]],
            "status": "generated"
        }
    
    def get_report_preview(self, report_id):
        """
        Récupère un aperçu d'un rapport généré.
        
        Args:
            report_id (str): Identifiant du rapport
            
        Returns:
            dict: Aperçu du rapport
        """
        # Rechercher le rapport dans l'historique
        for report in self.report_history:
            if report["report_id"] == report_id:
                # Dans une implémentation réelle, on chargerait le fichier
                # Pour cette simulation, on retourne les informations de l'historique
                return {
                    "report_id": report["report_id"],
                    "timestamp": report["timestamp"],
                    "parameters": report["parameters"],
                    "status": report["status"]
                }
        
        return None
    
    def get_available_templates(self):
        """
        Récupère la liste des modèles de rapport disponibles.
        
        Returns:
            dict: Modèles disponibles
        """
        return {
            template_name: {
                "sections": template["sections"],
                "description": self._get_template_description(template_name)
            }
            for template_name, template in self.templates.items()
        }
    
    def _get_template_description(self, template_name):
        """
        Génère une description pour un modèle de rapport.
        
        Args:
            template_name (str): Nom du modèle
            
        Returns:
            str: Description du modèle
        """
        if template_name == "standard":
            return "Rapport complet avec toutes les informations réglementaires"
        elif template_name == "simplified":
            return "Rapport simplifié avec les informations essentielles"
        else:
            return "Modèle de rapport personnalisé"
    
    def get_report_history(self, limit=10):
        """
        Récupère l'historique des rapports générés.
        
        Args:
            limit (int): Nombre maximum de rapports à récupérer
            
        Returns:
            list: Historique des rapports
        """
        return self.report_history[-limit:] if self.report_history else []
# 🚢 TraeFishing

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95.2-green.svg)](https://fastapi.tiangolo.com/)
[![GitHub](https://img.shields.io/badge/GitHub-blueMind-blue.svg)](https://github.com/Lehnin2/blueMind)

## 📋 Description

TraeFishing est une application maritime intelligente conçue pour les pêcheurs et navigateurs tunisiens. Elle combine des technologies de pointe en cartographie, météorologie, et intelligence artificielle pour offrir une expérience de navigation sécurisée et conforme à la réglementation maritime tunisienne.

![TraeFishing Dashboard](https://via.placeholder.com/800x400?text=TraeFishing+Dashboard)

## ✨ Fonctionnalités principales

### 🗺️ Navigation et cartographie
- **Planificateur de routes maritimes** - Calculez et visualisez des itinéraires optimisés entre deux points
- **Localisation en temps réel** - Suivez votre position actuelle sur une carte interactive
- **Carte des ports** - Accédez à une base de données complète des ports tunisiens
- **Recherche de ports à proximité** - Trouvez rapidement les ports les plus proches de votre position

### 📏 Outils de mesure et d'analyse
- **Estimation de profondeur** - Obtenez des données bathymétriques précises à n'importe quelle coordonnée
- **Vérificateur de zones** - Identifiez les zones protégées et les restrictions de pêche
- **Calcul de position** - Estimez de nouvelles coordonnées basées sur distance et cap

### 🌦️ Météorologie et astronomie
- **Prévisions météorologiques marines** - Accédez aux conditions météo actuelles et prévisions
- **Données astronomiques** - Consultez les heures de lever/coucher du soleil et phases lunaires
- **Alertes météo** - Recevez des notifications en temps réel sur les conditions dangereuses

### 🤖 Assistants IA intégrés
- **Assistant Contextuel Flottant** - Une bulle d'aide intelligente présente sur toutes les pages pour une assistance rapide
- **Chatbot Si Lba7ri Spécialisé** - Interface dédiée avec fonctionnalités avancées pour la navigation et la réglementation
- **Interface vocale multilingue** - Interagissez avec Si Lba7ri en tunisien, français, anglais ou italien
- **Reconnaissance vocale avancée** - Utilisez le microphone pour communiquer naturellement avec l'assistant
- **Synthèse vocale (TTS)** - Écoutez les réponses de Si Lba7ri grâce à la synthèse vocale
- **Mode maritime spécialisé** - Mode dédié aux questions maritimes pour des réponses plus précises
- **Assistant d'interface contextuel** - Bénéficiez d'une aide proactive sur chaque page
- **Recherche intelligente** - Interrogez la base de connaissances sur la législation maritime tunisienne
- **Mémoire contextuelle** - L'assistant se souvient de vos interactions précédentes pour des réponses plus pertinentes
- **Intégration avec les outils de navigation** - Demandez directement des informations sur les ports, la météo ou les zones protégées
- **Support dialecte tunisien** - Compréhension native du dialecte tunisien pour une meilleure accessibilité
- **Aide à la réglementation** - Assistance pour comprendre les lois maritimes tunisiennes en vigueur

### 🔐 Authentification sécurisée
- **Système d'authentification** - Protégez vos données avec Supabase
- **Profils personnalisés** - Sauvegardez vos préférences et historique de navigation

## 🛠️ Technologies utilisées

### Backend
- **FastAPI** - Framework Python moderne, rapide et asynchrone pour les API
- **Python 3.9+** - Langage de programmation puissant et flexible
- **Starlette** - Toolkit ASGI léger pour les applications web asynchrones
- **SSE-Starlette** - Extension pour les notifications en temps réel (Server-Sent Events)
- **WebSockets** - Protocole pour la communication bidirectionnelle en temps réel

### Intelligence Artificielle
- **LangChain** - Framework pour développer des applications alimentées par des LLM
- **FAISS** - Bibliothèque de recherche vectorielle pour l'indexation efficace
- **Groq** - API d'inférence ultra-rapide pour les modèles de langage
- **Web Speech API** - Interface pour la reconnaissance vocale et la synthèse vocale
- **BAAI/bge-m3** - Modèle d'embedding pour la recherche sémantique
- **Système de RAG (Retrieval-Augmented Generation)** - Améliore les réponses de l'IA avec des données spécifiques à la législation maritime tunisienne

### Cartographie et Données
- **Folium** - Bibliothèque Python pour créer des cartes interactives
- **Branca** - Extension pour Folium avec des fonctionnalités avancées
- **OpenCV** - Bibliothèque de traitement d'images pour l'analyse cartographique
- **Pillow** - Bibliothèque de manipulation d'images

### Frontend et Authentification
- **HTML5/CSS3/JavaScript** - Technologies web standard pour l'interface utilisateur
- **Supabase** - Plateforme open-source pour l'authentification et la gestion de base de données
- **Marked.js** - Bibliothèque pour le rendu Markdown dans le chatbot

### Architecture du système
- **Architecture modulaire** - Organisation en composants réutilisables
- **API RESTful** - Interface programmatique standardisée
- **WebSockets** - Communication bidirectionnelle en temps réel
- **Système de notifications** - Alertes en temps réel pour les conditions météorologiques

## 📦 Installation

### Prérequis
- Python 3.9 ou supérieur
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. Clonez le dépôt
```bash
git clone https://github.com/Lehnin2/blueMind.git traefishing
cd traefishing
```

2. Créez et activez un environnement virtuel
```bash
python -m venv venv
# Sur Windows
venv\Scripts\activate
# Sur macOS/Linux
source venv/bin/activate
```

3. Installez les dépendances
```bash
pip install -r requirements.txt
```

4. Configurez les variables d'environnement
```bash
# Créez un fichier .env à la racine du projet avec les variables suivantes
SUPABASE_URL=votre_url_supabase
SUPABASE_KEY=votre_cle_supabase
STORMGLASS_API_KEY=votre_cle_stormglass
GROQ_API_KEY=votre_cle_groq
```

5. Lancez l'application
```bash
python -m app.main
```

6. Accédez à l'application dans votre navigateur à l'adresse `http://localhost:8000`

## 📚 Documentation

La documentation complète est disponible dans le dossier `docs/` du projet. Consultez les guides suivants :

- [Guide d'authentification](app/auth/README.md)
- [Guide de contribution](CONTRIBUTING.md)

## 🤝 Contribution

Les contributions sont les bienvenues ! Consultez notre [guide de contribution](CONTRIBUTING.md) pour plus d'informations sur comment participer au projet.

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 📞 Contact

Pour toute question ou suggestion, n'hésitez pas à ouvrir une issue sur ce dépôt.

## 🔄 Développement

Pour contribuer au projet, veuillez créer une branche spécifique pour vos modifications :

```bash
# Créer une nouvelle branche
git checkout -b feature/ma-nouvelle-fonctionnalite

# Après avoir effectué vos modifications
git add .
git commit -m "Description détaillée de vos modifications"

# Pousser vers le dépôt distant
git push origin feature/ma-nouvelle-fonctionnalite
```

Ensuite, créez une Pull Request sur le dépôt [blueMind](https://github.com/Lehnin2/blueMind) pour que vos modifications soient examinées.

---

© 2023 TraeFishing. Tous droits réservés.
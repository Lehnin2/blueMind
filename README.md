# Assistance Réglementaire Pêche

Une application web complète pour informer, guider et assister les pêcheurs concernant les réglementations de pêche en vigueur. Cette plateforme utilise des technologies modernes et l'intelligence artificielle pour fournir une assistance personnalisée aux utilisateurs.

![Capture d'écran de l'application](https://via.placeholder.com/800x400?text=Assistance+Réglementaire+Pêche)

## 🌟 Fonctionnalités

- **Consultation des réglementations** par zone géographique et par espèce
- **Calendrier interactif** des périodes de pêche autorisées et interdites
- **Base de données d'espèces** avec informations sur les tailles minimales et quotas
- **Carte interactive** des zones de pêche avec statut réglementaire en temps réel
- **Assistant IA conversationnel** pour répondre aux questions réglementaires
- **Système de recherche avancé** pour trouver rapidement des informations spécifiques
- **Espace de contribution communautaire** pour partager des informations et expériences
- **Module d'apprentissage** pour se former aux bonnes pratiques de pêche
- **Génération de documents** et attestations conformes à la réglementation

## 🛠️ Technologies Utilisées

- **Backend**: FastAPI (Python 3.9+)
- **Frontend**: HTML5, CSS3, JavaScript avec templates Jinja2
- **Base de données**: SQLite (développement) / PostgreSQL (production)
- **Cartographie**: Folium (basé sur Leaflet)
- **IA & NLP**: 
  - LlamaIndex pour l'indexation et la recherche sémantique
  - FAISS pour le stockage vectoriel efficace
  - Modèles Hugging Face pour les embeddings (BGE)
  - API Gemini pour l'assistant conversationnel
- **Authentification**: Système de login sécurisé avec JWT

## 🏗️ Architecture du Projet

```
reglementation_peche/
├── app/                      # Code principal de l'application
│   ├── agents/              # Agents IA spécialisés
│   │   ├── community_agent.py
│   │   ├── generation_agent.py
│   │   ├── rag_agent.py
│   │   ├── reasoning_agent.py
│   │   ├── retrieval_agent.py
│   │   └── ...
│   ├── api/                 # Routes API
│   │   ├── routes.py
│   │   └── quiz_routes.py
│   └── static/              # Fichiers statiques
│       ├── css/
│       └── js/
├── data/                    # Données et documents réglementaires
│   └── loi.txt
├── templates/               # Templates HTML
│   ├── assistance.html
│   ├── base.html
│   ├── carte.html
│   └── ...
├── main.py                  # Point d'entrée de l'application
└── requirements.txt         # Dépendances Python
```

## 🚀 Installation et Démarrage

### Prérequis

- Python 3.9 ou supérieur
- pip (gestionnaire de paquets Python)
- Virtualenv (recommandé)

### Installation

1. Clonez ce dépôt :
   ```bash
   git clone https://github.com/votre-username/reglementation_peche.git
   cd reglementation_peche
   ```

2. Créez et activez un environnement virtuel :
   ```bash
   python -m venv venv
   
   # Sur Windows
   venv\Scripts\activate
   
   # Sur macOS/Linux
   source venv/bin/activate
   ```

3. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

4. Téléchargez les modèles linguistiques pour spaCy :
   ```bash
   python -m spacy download fr_core_news_md
   python -m spacy download en_core_web_sm
   ```

### Démarrage

1. Lancez l'application :
   ```bash
   uvicorn main:app --reload
   ```

2. Ouvrez votre navigateur et accédez à :
   ```
   http://localhost:8000
   ```

## 🔧 Configuration

Créez un fichier `.env` à la racine du projet avec les variables suivantes :

```env
# Configuration de l'application
DEBUG=True
SECRET_KEY=votre_clé_secrète_ici

# API Keys
GEMINI_API_KEY=votre_clé_api_gemini

# Base de données (pour la production)
DATABASE_URL=postgresql://user:password@localhost/db_name
```

## 🧪 Tests

Exécutez les tests avec pytest :

```bash
python -m pytest
```

## 🤝 Contribution

Les contributions sont les bienvenues ! Veuillez consulter le fichier [CONTRIBUTING.md](CONTRIBUTING.md) pour les directives de contribution.

## 📄 Licence

Ce projet est sous licence [MIT](LICENSE).

## 📞 Contact

Pour toute question ou suggestion, veuillez ouvrir une issue sur ce dépôt GitHub.

---

Développé avec ❤️ pour la communauté des pêcheurs responsables.
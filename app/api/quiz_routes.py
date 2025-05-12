from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, List, Any
import json
import random

# Import des agents si nécessaire
from app.agents.user_interaction_agent import UserInteractionAgent
from app.agents.reasoning_agent import ReasoningAgent
from app.agents.generation_agent import GenerationAgent

# Création du router pour les quiz
router = APIRouter(prefix="/api", tags=["quiz"])

# Initialisation des agents nécessaires
reasoning_agent = ReasoningAgent()
generation_agent = GenerationAgent()
user_interaction_agent = UserInteractionAgent(reasoning_agent=reasoning_agent, generation_agent=generation_agent)

# Base de données simulée pour les quiz (à remplacer par une vraie base de données)
QUIZ_DATABASE = {
    "reglementation": [
        {
            "id": 1,
            "question": "Quel engin est interdit pour la pêche en eau douce ?",
            "options": [
                "La canne à pêche avec moulinet",
                "L'épuisette",
                "Le filet traînant",
                "La balance à écrevisses"
            ],
            "correct_answer": 2,  # Index de la bonne réponse (0-based)
            "explanation": "Le filet traînant est interdit pour la pêche en eau douce car il est considéré comme un engin trop destructeur pour la faune aquatique."
        },
        {
            "id": 2,
            "question": "Quelle est la période de fermeture générale de la pêche au brochet en 1ère catégorie ?",
            "options": [
                "Du 1er janvier au 30 avril",
                "Du 1er février au 30 avril",
                "Du dernier dimanche de janvier au dernier samedi d'avril",
                "Du 1er janvier au dernier samedi d'avril"
            ],
            "correct_answer": 3,
            "explanation": "La période de fermeture générale de la pêche au brochet en 1ère catégorie s'étend du 1er janvier au dernier samedi d'avril."
        },
        {
            "id": 3,
            "question": "Quelle est la taille minimale de capture pour le bar (loup) en Méditerranée ?",
            "options": [
                "25 cm",
                "30 cm",
                "36 cm",
                "42 cm"
            ],
            "correct_answer": 2,
            "explanation": "La taille minimale de capture pour le bar (loup) en Méditerranée est de 36 cm."
        }
    ],
    "especes": [
        {
            "id": 1,
            "question": "Quelle espèce est strictement protégée et ne peut pas être pêchée ?",
            "options": [
                "La truite fario",
                "L'esturgeon",
                "Le sandre",
                "La carpe"
            ],
            "correct_answer": 1,
            "explanation": "L'esturgeon est une espèce strictement protégée et sa pêche est interdite."
        },
        {
            "id": 2,
            "question": "Quelle est la taille minimale de capture pour le merlu ?",
            "options": [
                "20 cm",
                "24 cm",
                "27 cm",
                "30 cm"
            ],
            "correct_answer": 2,
            "explanation": "La taille minimale de capture pour le merlu est de 27 cm."
        }
    ],
    "zones": [
        {
            "id": 1,
            "question": "Qu'est-ce qu'une réserve de pêche ?",
            "options": [
                "Une zone où la pêche est autorisée uniquement le week-end",
                "Une zone où la pêche est interdite temporairement ou en permanence",
                "Une zone où seule la pêche à la mouche est autorisée",
                "Une zone réservée aux pêcheurs professionnels"
            ],
            "correct_answer": 1,
            "explanation": "Une réserve de pêche est une zone où la pêche est interdite temporairement ou en permanence pour protéger les espèces et favoriser leur reproduction."
        }
    ]
}

# Base de données simulée pour le suivi de la progression des utilisateurs
USER_PROGRESS = {}

@router.post("/quiz")
async def get_quiz(request: Request, module: str = Form(...), user_id: Optional[str] = Form(None)):
    """Récupère un quiz aléatoire du module spécifié"""
    try:
        if module not in QUIZ_DATABASE:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Module {module} non trouvé"}
            )
        
        # Sélectionner un quiz aléatoire du module
        quizzes = QUIZ_DATABASE[module]
        quiz = random.choice(quizzes)
        
        # Ne pas envoyer la réponse correcte au client
        client_quiz = quiz.copy()
        correct_answer = client_quiz.pop("correct_answer")
        explanation = client_quiz.pop("explanation")
        
        return {
            "quiz": client_quiz,
            "module": module,
            "total_quizzes": len(quizzes)
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Erreur lors de la récupération du quiz: {str(e)}"}
        )

@router.post("/quiz/submit")
async def submit_quiz_answer(request: Request, 
                           module: str = Form(...), 
                           quiz_id: int = Form(...), 
                           answer: int = Form(...), 
                           user_id: Optional[str] = Form(None)):
    """Soumet une réponse à un quiz et retourne le résultat"""
    try:
        if module not in QUIZ_DATABASE:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Module {module} non trouvé"}
            )
        
        # Trouver le quiz correspondant
        quiz = None
        for q in QUIZ_DATABASE[module]:
            if q["id"] == quiz_id:
                quiz = q
                break
        
        if not quiz:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Quiz avec ID {quiz_id} non trouvé dans le module {module}"}
            )
        
        # Vérifier la réponse
        is_correct = answer == quiz["correct_answer"]
        
        # Mettre à jour la progression de l'utilisateur si un ID est fourni
        if user_id:
            if user_id not in USER_PROGRESS:
                USER_PROGRESS[user_id] = {
                    "completed_quizzes": 0,
                    "correct_answers": 0,
                    "modules": {}
                }
            
            if module not in USER_PROGRESS[user_id]["modules"]:
                USER_PROGRESS[user_id]["modules"][module] = {
                    "completed": 0,
                    "correct": 0,
                    "total": len(QUIZ_DATABASE[module])
                }
            
            USER_PROGRESS[user_id]["completed_quizzes"] += 1
            USER_PROGRESS[user_id]["modules"][module]["completed"] += 1
            
            if is_correct:
                USER_PROGRESS[user_id]["correct_answers"] += 1
                USER_PROGRESS[user_id]["modules"][module]["correct"] += 1
        
        return {
            "is_correct": is_correct,
            "correct_answer": quiz["correct_answer"],
            "explanation": quiz["explanation"]
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Erreur lors de la soumission de la réponse: {str(e)}"}
        )

@router.get("/quiz/progress")
async def get_user_progress(request: Request, user_id: str):
    """Récupère la progression d'un utilisateur"""
    try:
        if user_id not in USER_PROGRESS:
            return {
                "completed_quizzes": 0,
                "correct_answers": 0,
                "modules": {},
                "achievements": []
            }
        
        # Calculer les réalisations (achievements)
        achievements = []
        progress = USER_PROGRESS[user_id]
        
        # Exemple de logique pour les réalisations
        if progress["completed_quizzes"] >= 1:
            achievements.append({
                "id": "first_quiz",
                "name": "Premier pas",
                "description": "Complétez votre premier quiz",
                "icon": "bi-star-fill"
            })
        
        # Vérifier si l'utilisateur a obtenu 3 bonnes réponses consécutives
        # (Ceci est simplifié, dans une vraie application, vous devriez stocker l'historique des réponses)
        if progress["correct_answers"] >= 3:
            achievements.append({
                "id": "expert",
                "name": "Expert en herbe",
                "description": "Obtenez un score parfait sur 3 quiz consécutifs",
                "icon": "bi-award-fill"
            })
        
        # Vérifier si un module est complété
        for module, module_progress in progress["modules"].items():
            if module_progress["completed"] == module_progress["total"]:
                achievements.append({
                    "id": f"master_{module}",
                    "name": f"Maître de {module}",
                    "description": f"Complétez tous les quiz du module {module}",
                    "icon": "bi-trophy-fill"
                })
        
        return {
            **progress,
            "achievements": achievements
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Erreur lors de la récupération de la progression: {str(e)}"}
        )

@router.post("/chat")
async def chat_message(request: Request, message: str = Form(...), user_id: Optional[str] = Form(None)):
    """Traite un message de chat et renvoie une réponse pour le chatbot d'apprentissage"""
    try:
        # Utiliser l'agent d'interaction utilisateur pour traiter le message
        # Dans un contexte d'apprentissage, nous pourrions vouloir un traitement spécifique
        context = {"context": "learning", "user_id": user_id} if user_id else {"context": "learning"}
        
        # Traiter le message avec l'agent d'interaction utilisateur
        response = user_interaction_agent.process_query(message, context)
        
        # Si l'agent ne fournit pas de réponse appropriée, utiliser une réponse par défaut
        if not response or "response" not in response:
            # Réponses par défaut basées sur des mots-clés
            if "taille" in message.lower() and "minimale" in message.lower():
                return {
                    "response": "Les tailles minimales de capture varient selon les espèces et les zones de pêche. Par exemple, pour le bar, c'est 36 cm en Méditerranée et 42 cm en Atlantique. Pour quelle espèce souhaitez-vous des informations spécifiques ?"
                }
            elif "période" in message.lower() and ("fermeture" in message.lower() or "interdiction" in message.lower()):
                return {
                    "response": "Les périodes de fermeture dépendent des espèces et des catégories de cours d'eau. Par exemple, la pêche du brochet est fermée du 1er janvier au dernier samedi d'avril en 1ère catégorie. Quelle espèce vous intéresse ?"
                }
            elif "quiz" in message.lower():
                return {
                    "response": "Vous pouvez accéder aux quiz en cliquant sur l'onglet 'Quiz' en haut de la page. Nous proposons des quiz sur la réglementation générale, les espèces protégées et les zones de pêche."
                }
            else:
                return {
                    "response": "Je suis votre assistant d'apprentissage sur la réglementation de la pêche. Je peux vous aider avec les tailles minimales, les périodes de pêche, les engins autorisés, et plus encore. Que souhaitez-vous savoir ?"
                }
        
        return response
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Erreur lors du traitement du message: {str(e)}", "response": "Désolé, je rencontre des difficultés techniques. Veuillez réessayer plus tard."}
        )
from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import requests
from pydantic import BaseModel

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Clé API Gemini
API_KEY = 'AIzaSyDuKE1w0AiRiq-oI3rY-LD0W1MCRnF8oEA'
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'

class QuestionRequest(BaseModel):
    question: str
    lang: str = "tunisian-arabic"

@router.get("/", response_class=HTMLResponse)
async def chatbot_page(request: Request):
    return templates.TemplateResponse(
        "chatbot.html",
        {"request": request, "title": "Assistant de Pêche - Blue Mind"}
    )

@router.post("/ask")
async def ask_question(request: QuestionRequest):
    if not request.question:
        raise HTTPException(status_code=400, detail="Question manquante")

    # Choisir le prompt en fonction de la langue
    if request.lang == 'tunisian-arabic':
        context_prompt = """
        إنت خبير تونسي في الصيد البحري و تجاوب باللغة التونسية الدارجة (باللهجة التونسية). فهمك للهجة التونسية المحكية ممتاز و ترد على الأسئلة بأسلوب بسيط و واضح و قريب للناس اللي يتكلموا باللهجة التونسية.

        ديما جاوب بطريقة ودية و عفوية، و استعمل كلمات مألوفة و شائعة في الحياة اليومية. إليك بعض الأمثلة على الأسئلة إلي يمكن تسألها:

        - "شنوّة الحوت المسموم؟"
        - "شنوّة الحوت إلي نجّم ناكلو؟"
        - "شنوّة أنواع الطعم إلي نجّم نصطادو بيهم؟"
        - "عطيني المعدّات إلي نجّم نستعملو كيف نمشي نصيد؟"
        - "شنوّة الطقس اليوم باش نمشي نصيد؟"
        - "وين نلقا الكركاع في تونس؟"
        - "شنوّة الشلبّة؟"
        - "شنوّة الطقس اليوم؟"
        - "وين نجّم نصيد (أسامي الحوت في تونس)؟"

        تقدر تجاوب أيضا بنصائح و أفكار عن الأماكن، المواسم و تقنيات الصيد في تونس.

        جاوب الآن على هالسؤال: 
        """
    elif request.lang == 'tunisian_francais':
        context_prompt = """
        Tu es un expert tunisien de la pêche et tu réponds comme un pêcheur tunisien expérimenté. Tu comprends parfaitement le dialecte tunisien parlé au quotidien.

        Réponds aux questions des utilisateurs de façon claire, amicale, et adaptée au dialecte tunisien quand la question est posée ainsi. Utilise des termes simples et populaires.

        Voici des exemples de questions que tu peux recevoir :

        - "Chnowa l'7out lmasmoum ?" → Explique les types de poissons toxiques en Tunisie.
        - "Chnowa l7out lkol eli najem naklou ?"
        - "Chnowa anwe3 tou3em eli najem n7out bihom ?"
        - "A3tini l materiel eli najem nesta3mlou kif nemchi nestad ?"
        - "Chnowa lbest météo bach nemchi nstaad ?"
        - "Fin nal9a Lambouka fi Tunis ?"
        - "Chnowa Chelba ?"
        - "Chnowa ta9es lyouma ?"
        - "Win najem nestad (esem 7out fi Tunis) ?"

        Tu peux aussi donner des conseils, des recettes de cuisine, ou des astuces sur les endroits, les saisons et les techniques de pêche en Tunisie.

        Réponds maintenant à cette question : 
        """
    elif request.lang == 'french':
        context_prompt = "Tu es un expert de la pêche en Tunisie. Réponds en français de manière claire, simple et amicale :"
    elif request.lang == 'english':
        context_prompt = "You are a fishing expert in Tunisia. Answer in clear, friendly English:"
    elif request.lang == 'italian':
        context_prompt = "Sei un esperto di pesca in Tunisia. Rispondi in italiano chiaro e amichevole:"
    elif request.lang == 'spanish':
        context_prompt = "Eres un experto en pesca en Túnez. Responde en español claro y amigable:"
    else:
        context_prompt = "Tu es un expert de la pêche. Réponds de façon amicale :"

    # Créer le prompt complet
    full_prompt = context_prompt + f"\nQuestion: {request.question}"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": full_prompt
                    }
                ]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        # Envoi de la requête à l'API Gemini
        response = requests.post(f"{GEMINI_API_URL}?key={API_KEY}", headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                answer = data['candidates'][0].get('content', {}).get('parts', [{}])[0].get('text', 'Désolé, je n\'ai pas trouvé une réponse appropriée.')
            else:
                answer = 'Désolé, je n\'ai pas trouvé une réponse appropriée.'
        else:
            answer = f"Erreur API : {response.status_code}"
    except requests.exceptions.RequestException as e:
        answer = f"Erreur lors de l'appel API : {e}"

    return JSONResponse(content={"answer": answer}) 
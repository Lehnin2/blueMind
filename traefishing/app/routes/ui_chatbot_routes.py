from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from agent_router import AgentRouter

# Créer un router pour les routes du chatbot UI
router = APIRouter()

# Initialiser l'agent router qui contient le UI chatbot
agent_router = AgentRouter()

@router.post("/api/ui-chatbot")
async def ui_chatbot_api(request: Request):
    """API endpoint pour le chatbot contextuel d'interface"""
    try:
        data = await request.json()
        message = data.get('message', '')
        
        if not message:
            return JSONResponse({"error": "Aucun message fourni"}, status_code=400)
        
        # Utiliser le UI chatbot pour traiter le message
        response = agent_router.handle_ui_message(message)
        return JSONResponse(response)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
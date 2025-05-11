from flask import Blueprint
from app.websocket_handler import dashboard_ws

ws_blueprint = Blueprint('websocket', __name__)

@ws_blueprint.websocket('/ws/dashboard')
async def dashboard_websocket():
    websocket = ws_blueprint.websocket
    try:
        await dashboard_ws.register(websocket)
        while True:
            try:
                # Wait for any message from the client
                await websocket.receive()
            except Exception:
                break
    finally:
        await dashboard_ws.unregister(websocket)
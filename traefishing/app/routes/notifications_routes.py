from fastapi import APIRouter, Response
from sse_starlette.sse import EventSourceResponse
from typing import AsyncGenerator
import asyncio

router = APIRouter()

async def notification_generator() -> AsyncGenerator[str, None]:
    """Générateur de notifications pour le flux SSE."""
    while True:
        # Simuler une notification toutes les 30 secondes
        await asyncio.sleep(30)
        yield {
            "event": "notification",
            "data": "Nouvelle mise à jour disponible"
        }

@router.get("/api/notifications/stream")
async def stream_notifications():
    """Endpoint pour le flux de notifications en temps réel."""
    return EventSourceResponse(notification_generator())

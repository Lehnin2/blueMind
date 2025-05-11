# Ce fichier est conservé pour compatibilité mais n'est plus utilisé activement
# Les données d'astronomie et météo sont maintenant fournies via l'API REST
# Voir la route /api/astro-weather dans main.py

import asyncio
import json

class DashboardWebSocket:
    """Classe de compatibilité pour les anciennes connexions WebSocket.
    Cette classe est maintenue pour éviter les erreurs mais n'effectue plus de mises à jour actives.
    Les données sont maintenant fournies via l'API REST."""
    
    def __init__(self):
        self.clients = set()
        self.update_task = None
    
    async def register(self, websocket):
        """Enregistre un client WebSocket mais n'initialise pas de tâche de mise à jour."""
        self.clients.add(websocket)
        # Informer le client que cette méthode est dépréciée
        try:
            await websocket.send(json.dumps({
                'deprecated': True,
                'message': 'WebSocket API is deprecated. Please use the REST API endpoint /api/astro-weather instead.'
            }))
        except Exception as e:
            print(f'Error sending deprecation notice: {e}')
    
    async def unregister(self, websocket):
        """Désenregistre un client WebSocket."""
        if websocket in self.clients:
            self.clients.remove(websocket)

# Instance maintenue pour compatibilité
dashboard_ws = DashboardWebSocket()
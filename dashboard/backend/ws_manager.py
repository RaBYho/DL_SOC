import json
import logging
from typing import Any, Dict, List
from fastapi import WebSocket

logger = logging.getLogger("dashboard.ws")


class ConnectionManager:
    """Gestionnaire de connexions WebSocket pour diffuser les alertes réseau en temps réel."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client WebSocket connecté. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                f"Client WebSocket déconnecté. Restants: {len(self.active_connections)}"
            )

    async def send_personal_message(
        self, message: Dict[str, Any], websocket: WebSocket
    ) -> None:
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Erreur envoi message individuel: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Diffuse un événement JSON à l'ensemble des navigateurs connectés."""
        if not self.active_connections:
            return

        payload = json.dumps(message)
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.warning(f"Erreur lors du broadcast WebSocket: {e}")
                disconnected.append(connection)

        for dead_conn in disconnected:
            self.disconnect(dead_conn)


ws_manager = ConnectionManager()

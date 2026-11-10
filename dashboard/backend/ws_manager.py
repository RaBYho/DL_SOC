"""WebSocket connection manager for real-time SOC dashboard telemetry and alerts."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import Any
from fastapi import WebSocket

logger = logging.getLogger("dashboard.ws")


class WebSocketManager:
    """Manages active WebSocket connections and handles real-time broadcasting."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accepts and registers a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total active: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """Removes a disconnected WebSocket client."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: Any) -> None:
        """Broadcasts an event message with ISO-8601 UTC timestamp to all connected clients."""
        payload = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.broadcast_raw(payload)

    async def broadcast_raw(self, payload: dict[str, Any]) -> None:
        """Broadcasts a raw dictionary payload formatted as JSON to all active connections."""
        if not self.active_connections:
            return

        text_data = json.dumps(payload, default=str)
        dead_connections: list[WebSocket] = []

        async with self._lock:
            connections = list(self.active_connections)

        for ws in connections:
            try:
                await ws.send_text(text_data)
            except Exception as exc:
                logger.debug(f"Failed to send to client ({exc}). Marking for cleanup.")
                dead_connections.append(ws)

        if dead_connections:
            async with self._lock:
                for ws in dead_connections:
                    if ws in self.active_connections:
                        self.active_connections.remove(ws)


ws_manager = WebSocketManager()

from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    """Manages active native WebSocket connections for live match scoring broadcasts."""

    def __init__(self) -> None:
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, match_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if match_id not in self.active_connections:
            self.active_connections[match_id] = []
        self.active_connections[match_id].append(websocket)

    def disconnect(self, match_id: str, websocket: WebSocket) -> None:
        if match_id in self.active_connections:
            if websocket in self.active_connections[match_id]:
                self.active_connections[match_id].remove(websocket)
            if not self.active_connections[match_id]:
                del self.active_connections[match_id]

    async def broadcast_match(self, match_id: str, message: dict) -> None:
        if match_id in self.active_connections:
            for connection in list(self.active_connections[match_id]):
                try:
                    await connection.send_json(message)
                except Exception:
                    self.disconnect(match_id, connection)


manager = ConnectionManager()


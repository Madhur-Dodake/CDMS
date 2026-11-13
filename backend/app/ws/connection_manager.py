import asyncio
from typing import Any, Dict, List, Optional
from fastapi import WebSocket


class ConnectionManager:
    """Manages active native WebSocket connections per match_id room."""

    def __init__(self) -> None:
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    async def connect(self, match_id: str, websocket: WebSocket) -> None:
        """Accept WebSocket connection and register in match_id room."""
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            pass

        await websocket.accept()
        if match_id not in self.active_connections:
            self.active_connections[match_id] = []
        if websocket not in self.active_connections[match_id]:
            self.active_connections[match_id].append(websocket)

    def disconnect(self, match_id: str, websocket: WebSocket) -> None:
        """Remove WebSocket connection from match_id room."""
        if match_id in self.active_connections:
            if websocket in self.active_connections[match_id]:
                self.active_connections[match_id].remove(websocket)
            if not self.active_connections[match_id]:
                del self.active_connections[match_id]

    async def broadcast(self, match_id: str, message: dict) -> None:
        """Broadcast JSON message to all connected clients in match_id room."""
        if match_id in self.active_connections:
            dead_connections: List[WebSocket] = []
            for connection in list(self.active_connections[match_id]):
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.append(connection)
            for dead in dead_connections:
                self.disconnect(match_id, dead)

    async def broadcast_match(self, match_id: str, message: dict) -> None:
        """Alias for broadcast for backward compatibility."""
        await self.broadcast(match_id, message)

    def broadcast_sync(self, match_id: str, message: dict) -> None:
        """Synchronously broadcast to match_id room from sync thread or async task."""
        # 1. Try anyio.from_thread when inside FastAPI's worker thread pool
        try:
            import anyio.from_thread

            anyio.from_thread.run(self.broadcast, match_id, message)
            return
        except Exception:
            pass

        # 2. Try current running event loop
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(match_id, message))
            return
        except RuntimeError:
            pass

        # 3. Try stored main loop if available and running
        if self.loop and self.loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(self.broadcast(match_id, message), self.loop)
                return
            except Exception:
                pass

        # 4. Fallback: run in a new loop
        try:
            asyncio.run(self.broadcast(match_id, message))
        except Exception:
            pass

    async def ping_all(self, match_id: Optional[str] = None) -> None:
        """Heartbeat / ping connected clients to keep connection alive and purge dead sockets."""
        targets = [match_id] if match_id and match_id in self.active_connections else list(self.active_connections.keys())
        for m_id in targets:
            dead_connections: List[WebSocket] = []
            for connection in list(self.active_connections.get(m_id, [])):
                try:
                    await connection.send_text("ping")
                except Exception:
                    dead_connections.append(connection)
            for dead in dead_connections:
                self.disconnect(m_id, dead)


manager = ConnectionManager()

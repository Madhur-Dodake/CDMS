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

    def _try_anyio_thread(self, match_id: str, message: dict) -> bool:
        """Attempt broadcasting through AnyIO worker thread."""
        try:
            import anyio.from_thread

            anyio.from_thread.run(self.broadcast, match_id, message)
            return True
        except Exception:
            return False

    def _try_current_loop(self, match_id: str, message: dict) -> bool:
        """Attempt broadcasting via current running event loop task."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(match_id, message))
            return True
        except RuntimeError:
            return False

    def _try_stored_loop(self, match_id: str, message: dict) -> bool:
        """Attempt broadcasting via threadsafe call to stored main loop."""
        if self.loop and self.loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(self.broadcast(match_id, message), self.loop)
                return True
            except Exception:
                pass
        return False

    def broadcast_sync(self, match_id: str, message: dict) -> None:
        """Synchronously broadcast to match_id room from sync thread or async task."""
        if self._try_anyio_thread(match_id, message):
            return

        if self._try_current_loop(match_id, message):
            return

        if self._try_stored_loop(match_id, message):
            return

        try:
            asyncio.run(self.broadcast(match_id, message))
        except Exception:
            pass

    async def _ping_room(self, room_id: str) -> None:
        """Ping all sockets in a room and prune unresponsive connections."""
        dead_connections: List[WebSocket] = []
        for connection in list(self.active_connections.get(room_id, [])):
            try:
                await connection.send_text("ping")
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            self.disconnect(room_id, dead)

    async def ping_all(self, match_id: Optional[str] = None) -> None:
        """Heartbeat / ping connected clients to keep connection alive and purge dead sockets."""
        if match_id and match_id in self.active_connections:
            await self._ping_room(match_id)
        else:
            for m_id in list(self.active_connections.keys()):
                await self._ping_room(m_id)


manager = ConnectionManager()

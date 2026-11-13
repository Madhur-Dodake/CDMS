from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.health import router as health_router
from app.api.matches import router as matches_router
from app.api.players import router as players_router
from app.api.teams import router as teams_router
from app.api.tournaments import router as tournaments_router
from app.api.users import router as users_router
from app.api.venues import router as venues_router
from app.schemas.health import HealthResponse
from app.ws.connection_manager import manager

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Cricket Data Management System (CDMS) Backend API",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(venues_router, prefix="/api")
app.include_router(teams_router, prefix="/api")
app.include_router(tournaments_router, prefix="/api")
app.include_router(players_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(matches_router, prefix="/api")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def root_health() -> HealthResponse:
    """Root health check endpoint."""
    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc),
    )


@app.websocket("/ws/matches/{match_id}")
async def websocket_match_endpoint(websocket: WebSocket, match_id: str) -> None:
    """Native FastAPI WebSocket connection endpoint for real-time live match updates."""
    await manager.connect(match_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(match_id, websocket)

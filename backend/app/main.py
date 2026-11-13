import json
import logging
import uuid
from datetime import datetime, timezone
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.logging_middleware import RequestLoggingMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.health import router as health_router
from app.api.matches import router as matches_router
from app.api.players import router as players_router
from app.api.scoring import router as scoring_router
from app.api.teams import router as teams_router
from app.api.tournaments import router as tournaments_router
from app.api.users import router as users_router
from app.api.venues import router as venues_router
from app.schemas.health import HealthResponse
from app.services import scoring_service
from app.ws.connection_manager import manager

logger = logging.getLogger("cdms.error")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Cricket Data Management System (CDMS) Backend API",
)

# 1. Security Headers Middleware (OWASP protection)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Structured Request Logging Middleware
app.add_middleware(RequestLoggingMiddleware)

# 3. CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"],
)


# Global Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Format Pydantic schema validation failures with clean messages."""
    errors = []
    for err in exc.errors():
        field_path = " -> ".join(str(loc) for loc in err.get("loc", []))
        errors.append(f"{field_path}: {err.get('msg')}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "; ".join(errors), "error_code": "VALIDATION_ERROR"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Standardize HTTP exception responses."""
    headers = exc.headers or {}
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all unhandled exception handler: prevents stack trace leakage."""
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error. Please try again later.", "error_code": "INTERNAL_SERVER_ERROR"},
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
app.include_router(scoring_router, prefix="/api")


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
async def websocket_match_endpoint(
    websocket: WebSocket,
    match_id: str,
    db: Session = Depends(get_db),
) -> None:
    """Native FastAPI WebSocket connection endpoint for real-time live match updates for viewers."""
    await manager.connect(match_id, websocket)

    # Send current snapshot immediately on connect
    try:
        match_uuid = uuid.UUID(match_id)
        snapshot = scoring_service.get_match_snapshot(db, match_uuid)
    except (ValueError, AttributeError):
        snapshot = None

    if snapshot is not None:
        await websocket.send_json(snapshot)
    else:
        # Match not found in DB: send basic not-found snapshot
        await websocket.send_json({
            "match_id": match_id,
            "status": "not_found",
            "score": 0,
            "wickets": 0,
            "overs": "0.0",
            "run_rate": 0.0,
            "required_rate": None,
            "target": None,
            "striker": None,
            "non_striker": None,
            "bowler": None,
            "last_ball": None,
            "recent_balls": [],
        })

    # Event listening loop for client messages and heartbeats
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            else:
                try:
                    msg = json.loads(data)
                    if isinstance(msg, dict) and msg.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except Exception:
                    pass
    except WebSocketDisconnect:
        manager.disconnect(match_id, websocket)
    except Exception:
        manager.disconnect(match_id, websocket)

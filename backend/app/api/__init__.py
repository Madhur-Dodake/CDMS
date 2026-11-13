"""API routers package."""
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.health import router as health_router
from app.api.matches import router as matches_router
from app.api.players import router as players_router
from app.api.teams import router as teams_router
from app.api.tournaments import router as tournaments_router
from app.api.users import router as users_router
from app.api.venues import router as venues_router

__all__ = [
    "health_router",
    "auth_router",
    "venues_router",
    "teams_router",
    "tournaments_router",
    "players_router",
    "users_router",
    "dashboard_router",
    "matches_router",
]

from __future__ import annotations

from fastapi import FastAPI

from app.config import get_settings
from app.database import Database
from app.migrations import run_migrations
from app.users.repository import UserRepository
from app.users.router import router as users_router


def create_app() -> FastAPI:
    settings = get_settings()
    run_migrations(settings.database_path)
    database = Database(settings.database_path)

    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.state.settings = settings
    app.state.database = database
    app.state.user_repository = UserRepository(database)
    app.include_router(users_router)

    @app.get("/health", tags=["System"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app

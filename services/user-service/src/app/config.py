from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str
    database_path: str
    jwt_secret: str
    jwt_algorithm: str
    jwt_expiration_minutes: int


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Survey Platform API"),
        database_path=os.getenv("DATABASE_URL", "data/survey_platform.db"),
        jwt_secret=os.getenv("JWT_SECRET", "change-me-in-production"),
        jwt_algorithm="HS256",
        jwt_expiration_minutes=int(os.getenv("JWT_EXPIRATION_MINUTES", "60")),
    )


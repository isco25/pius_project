from __future__ import annotations

from pathlib import Path

from alembic.config import Config

from alembic import command
from app.database import ensure_database_directory

SERVICE_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = SERVICE_ROOT / "alembic.ini"
ALEMBIC_SCRIPT_LOCATION = SERVICE_ROOT / "alembic"


def _to_sqlalchemy_url(database_path: str) -> str:
    if "://" in database_path:
        return database_path
    if database_path == ":memory:":
        return "sqlite:///:memory:"
    return f"sqlite:///{Path(database_path).as_posix()}"


def run_migrations(database_path: str, target_revision: str = "head") -> None:
    ensure_database_directory(database_path)

    config = Config(str(ALEMBIC_INI_PATH))
    config.set_main_option("script_location", str(ALEMBIC_SCRIPT_LOCATION))
    config.set_main_option("sqlalchemy.url", _to_sqlalchemy_url(database_path))
    command.upgrade(config, target_revision)

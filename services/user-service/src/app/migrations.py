from __future__ import annotations

import sqlite3
from pathlib import Path

from alembic.config import Config

from alembic import command
from app.database import ensure_database_directory, normalize_database_path

SERVICE_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = SERVICE_ROOT / "alembic.ini"
ALEMBIC_SCRIPT_LOCATION = SERVICE_ROOT / "alembic"
INITIAL_REVISION = "0001_create_users_table"


def _to_sqlalchemy_url(database_path: str) -> str:
    if "://" in database_path:
        return database_path
    if database_path == ":memory:":
        return "sqlite:///:memory:"
    return f"sqlite:///{Path(database_path).as_posix()}"


def _needs_legacy_stamp(database_path: str) -> bool:
    normalized_path = normalize_database_path(database_path)
    if normalized_path == ":memory:":
        return False

    database_file = Path(normalized_path)
    if not database_file.exists():
        return False

    with sqlite3.connect(database_file) as connection:
        row = connection.execute(
            """
            SELECT
                EXISTS(SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'users'),
                EXISTS(
                    SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'alembic_version'
                )
            """
        ).fetchone()

    if row is None:
        return False

    users_exists, alembic_version_exists = row
    return bool(users_exists) and not bool(alembic_version_exists)


def run_migrations(database_path: str, target_revision: str = "head") -> None:
    ensure_database_directory(database_path)

    config = Config(str(ALEMBIC_INI_PATH))
    config.set_main_option("script_location", str(ALEMBIC_SCRIPT_LOCATION))
    config.set_main_option("sqlalchemy.url", _to_sqlalchemy_url(database_path))
    if _needs_legacy_stamp(database_path):
        command.stamp(config, INITIAL_REVISION)
    command.upgrade(config, target_revision)

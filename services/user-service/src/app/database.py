from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy.engine import make_url


class Database:
    def __init__(self, db_path: str) -> None:
        self.db_path = normalize_database_path(db_path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()


def normalize_database_path(database_path: str) -> str:
    if "://" not in database_path:
        return database_path

    url = make_url(database_path)
    if url.get_backend_name() != "sqlite":
        raise ValueError("User service supports only SQLite databases")

    return url.database or ":memory:"


def ensure_database_directory(database_path: str) -> None:
    normalized_path = normalize_database_path(database_path)
    if normalized_path == ":memory:":
        return

    Path(normalized_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

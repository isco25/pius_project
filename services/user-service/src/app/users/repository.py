from __future__ import annotations

import sqlite3

from app.database import Database
from app.users.models import User


class UserRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(self, email: str, password_hash: str) -> User:
        with self.database.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash),
            )
            connection.commit()
            user_id = cursor.lastrowid
            row = connection.execute(
                "SELECT id, email, password_hash FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            raise sqlite3.IntegrityError("Failed to create user")
        return self._map_user(row)

    def get_by_email(self, email: str) -> User | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT id, email, password_hash FROM users WHERE email = ?",
                (email,),
            ).fetchone()
        return self._map_user(row) if row is not None else None

    def get_by_id(self, user_id: int) -> User | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT id, email, password_hash FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        return self._map_user(row) if row is not None else None

    @staticmethod
    def _map_user(row: sqlite3.Row) -> User:
        return User(
            id=int(row["id"]),
            email=str(row["email"]),
            password_hash=str(row["password_hash"]),
        )


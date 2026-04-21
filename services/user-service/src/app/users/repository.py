from __future__ import annotations

import sqlite3

from app.database import Database
from app.users.models import (
    EVENT_STATUS_PENDING,
    EventCreationResult,
    IdempotencyKeyRecord,
    ProcessedEvent,
    User,
)


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
                "SELECT id, email, password_hash, xp, level FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            raise sqlite3.IntegrityError("Failed to create user")
        return self._map_user(row)

    def get_by_email(self, email: str) -> User | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT id, email, password_hash, xp, level FROM users WHERE email = ?",
                (email,),
            ).fetchone()
        return self._map_user(row) if row is not None else None

    def get_by_id(self, user_id: int) -> User | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT id, email, password_hash, xp, level FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        return self._map_user(row) if row is not None else None

    def update_xp_and_level(self, user_id: int, xp: int, level: int) -> User | None:
        with self.database.connect() as connection:
            cursor = connection.execute(
                "UPDATE users SET xp = ?, level = ? WHERE id = ?",
                (xp, level, user_id),
            )
            connection.commit()
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                "SELECT id, email, password_hash, xp, level FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        return self._map_user(row) if row is not None else None

    def get_leaderboard(self, limit: int = 10, offset: int = 0) -> list[User]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, email, password_hash, xp, level
                FROM users
                ORDER BY xp DESC, level DESC, id ASC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        return [self._map_user(row) for row in rows]

    def get_idempotency_key(self, key: str) -> IdempotencyKeyRecord | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id, "key", answer_id, user_id, status, response_xp, response_level, created_at
                FROM idempotency_keys
                WHERE "key" = ?
                """,
                (key,),
            ).fetchone()
        return self._map_idempotency_key(row) if row is not None else None

    def get_event_by_answer_id(self, answer_id: int) -> ProcessedEvent | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id, answer_id, user_id, xp_awarded, status, result_xp, result_level, created_at
                FROM processed_events
                WHERE answer_id = ?
                """,
                (answer_id,),
            ).fetchone()
        return self._map_processed_event(row) if row is not None else None

    def create_idempotent_event(
        self,
        answer_id: int,
        user_id: int,
        idempotency_key: str | None = None,
    ) -> EventCreationResult:
        with self.database.connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """
                    INSERT INTO processed_events (answer_id, user_id, xp_awarded, status)
                    VALUES (?, ?, 0, ?)
                    """,
                    (answer_id, user_id, EVENT_STATUS_PENDING),
                )
                if idempotency_key is not None:
                    connection.execute(
                        """
                        INSERT INTO idempotency_keys ("key", answer_id, user_id, status)
                        VALUES (?, ?, ?, ?)
                        """,
                        (idempotency_key, answer_id, user_id, EVENT_STATUS_PENDING),
                    )
                connection.commit()
            except sqlite3.IntegrityError:
                connection.rollback()
                return EventCreationResult(
                    created=False,
                    event=self.get_event_by_answer_id(answer_id),
                    idempotency_record=(
                        self.get_idempotency_key(idempotency_key)
                        if idempotency_key is not None
                        else None
                    ),
                )

        return EventCreationResult(
            created=True,
            event=self.get_event_by_answer_id(answer_id),
            idempotency_record=(
                self.get_idempotency_key(idempotency_key)
                if idempotency_key is not None
                else None
            ),
        )

    def remember_idempotency_key(
        self,
        key: str,
        answer_id: int,
        user_id: int,
        status: str,
        response_xp: int | None = None,
        response_level: int | None = None,
    ) -> IdempotencyKeyRecord | None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO idempotency_keys (
                    "key", answer_id, user_id, status, response_xp, response_level
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (key, answer_id, user_id, status, response_xp, response_level),
            )
            connection.commit()
        return self.get_idempotency_key(key)

    def update_event_status(
        self,
        answer_id: int,
        status: str,
        xp_awarded: int | None = None,
        result_xp: int | None = None,
        result_level: int | None = None,
        idempotency_key: str | None = None,
    ) -> ProcessedEvent | None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE processed_events
                SET
                    xp_awarded = COALESCE(?, xp_awarded),
                    status = ?,
                    result_xp = COALESCE(?, result_xp),
                    result_level = COALESCE(?, result_level)
                WHERE answer_id = ?
                """,
                (xp_awarded, status, result_xp, result_level, answer_id),
            )
            if idempotency_key is not None:
                connection.execute(
                    """
                    UPDATE idempotency_keys
                    SET
                        status = ?,
                        response_xp = COALESCE(?, response_xp),
                        response_level = COALESCE(?, response_level)
                    WHERE "key" = ?
                    """,
                    (status, result_xp, result_level, idempotency_key),
                )
            connection.commit()
        return self.get_event_by_answer_id(answer_id)

    @staticmethod
    def _map_user(row: sqlite3.Row) -> User:
        return User(
            id=int(row["id"]),
            email=str(row["email"]),
            password_hash=str(row["password_hash"]),
            xp=int(row["xp"]),
            level=int(row["level"]),
        )

    @staticmethod
    def _map_processed_event(row: sqlite3.Row) -> ProcessedEvent:
        return ProcessedEvent(
            id=int(row["id"]),
            answer_id=int(row["answer_id"]),
            user_id=int(row["user_id"]),
            xp_awarded=int(row["xp_awarded"]),
            status=str(row["status"]),
            result_xp=int(row["result_xp"]) if row["result_xp"] is not None else None,
            result_level=(
                int(row["result_level"]) if row["result_level"] is not None else None
            ),
            created_at=str(row["created_at"]),
        )

    @staticmethod
    def _map_idempotency_key(row: sqlite3.Row) -> IdempotencyKeyRecord:
        return IdempotencyKeyRecord(
            id=int(row["id"]),
            key=str(row["key"]),
            answer_id=int(row["answer_id"]),
            user_id=int(row["user_id"]),
            status=str(row["status"]),
            response_xp=(
                int(row["response_xp"]) if row["response_xp"] is not None else None
            ),
            response_level=(
                int(row["response_level"]) if row["response_level"] is not None else None
            ),
            created_at=str(row["created_at"]),
        )

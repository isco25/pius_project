from __future__ import annotations

import sqlite3

from app.config import Settings
from app.security import create_access_token, hash_password, verify_password
from app.users.models import (
    EVENT_STATUS_COMPLETED,
    EVENT_STATUS_FAILED,
    EVENT_STATUS_PENDING,
    IdempotencyKeyRecord,
    ProcessedEvent,
    User,
    XpAwardResult,
)
from app.users.repository import UserRepository


class UserService:
    def __init__(self, repository: UserRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings

    def register_user(self, email: str, password: str) -> User:
        if self.repository.get_by_email(email) is not None:
            raise ValueError("User with this email already exists")

        try:
            return self.repository.create(email=email, password_hash=hash_password(password))
        except sqlite3.IntegrityError as error:
            raise ValueError("User with this email already exists") from error

    def login_user(self, email: str, password: str) -> str:
        user = self.repository.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise PermissionError("Invalid email or password")

        return create_access_token(
            subject=user.id,
            secret=self.settings.jwt_secret,
            expires_minutes=self.settings.jwt_expiration_minutes,
            algorithm=self.settings.jwt_algorithm,
        )

    def get_user(self, user_id: int) -> User:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise LookupError("User not found")
        return user

    def add_xp(
        self,
        user_id: int,
        answer_id: int,
        idempotency_key: str | None = None,
        amount: int = 5,
    ) -> XpAwardResult:
        if idempotency_key is not None:
            existing_key = self.repository.get_idempotency_key(idempotency_key)
            if existing_key is not None:
                return self._replay_from_idempotency_key(existing_key)

        existing_event = self.repository.get_event_by_answer_id(answer_id)
        if existing_event is not None:
            return self._replay_from_event(existing_event, idempotency_key)

        creation_result = self.repository.create_idempotent_event(
            answer_id=answer_id,
            user_id=user_id,
            idempotency_key=idempotency_key,
        )
        if not creation_result.created:
            if idempotency_key is not None:
                existing_key = self.repository.get_idempotency_key(idempotency_key)
                if existing_key is not None:
                    return self._replay_from_idempotency_key(existing_key)

            existing_event = self.repository.get_event_by_answer_id(answer_id)
            if existing_event is not None:
                return self._replay_from_event(existing_event, idempotency_key)

            raise RuntimeError("Failed to create event processing record")

        try:
            user = self.get_user(user_id)
            new_xp = user.xp + amount
            new_level = new_xp // 100
            updated_user = self.repository.update_xp_and_level(
                user_id=user_id,
                xp=new_xp,
                level=new_level,
            )
            if updated_user is None:
                raise LookupError("User not found")

            self.repository.update_event_status(
                answer_id=answer_id,
                status=EVENT_STATUS_COMPLETED,
                xp_awarded=amount,
                result_xp=updated_user.xp,
                result_level=updated_user.level,
                idempotency_key=idempotency_key,
            )
            return XpAwardResult(
                user=updated_user,
                is_duplicate=False,
                status=EVENT_STATUS_COMPLETED,
            )
        except LookupError:
            self.repository.update_event_status(
                answer_id=answer_id,
                status=EVENT_STATUS_FAILED,
                idempotency_key=idempotency_key,
            )
            raise
        except Exception as error:
            self.repository.update_event_status(
                answer_id=answer_id,
                status=EVENT_STATUS_FAILED,
                idempotency_key=idempotency_key,
            )
            raise RuntimeError("Failed to process answer-created event") from error

    def get_leaderboard(self, limit: int = 10, offset: int = 0) -> list[User]:
        return self.repository.get_leaderboard(limit=limit, offset=offset)

    def _replay_from_idempotency_key(self, record: IdempotencyKeyRecord) -> XpAwardResult:
        if record.status == EVENT_STATUS_FAILED:
            raise RuntimeError("Event processing previously failed")
        if record.status == EVENT_STATUS_PENDING:
            raise RuntimeError("Event is already being processed")

        user = self.get_user(record.user_id)
        replay_user = User(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
            xp=record.response_xp if record.response_xp is not None else user.xp,
            level=record.response_level if record.response_level is not None else user.level,
        )
        return XpAwardResult(
            user=replay_user,
            is_duplicate=True,
            status=record.status,
        )

    def _replay_from_event(
        self,
        event: ProcessedEvent,
        idempotency_key: str | None = None,
    ) -> XpAwardResult:
        if event.status == EVENT_STATUS_FAILED:
            raise RuntimeError("Event processing previously failed")
        if event.status == EVENT_STATUS_PENDING:
            raise RuntimeError("Event is already being processed")

        user = self.get_user(event.user_id)
        replay_user = User(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
            xp=event.result_xp if event.result_xp is not None else user.xp,
            level=event.result_level if event.result_level is not None else user.level,
        )

        if idempotency_key is not None:
            self.repository.remember_idempotency_key(
                key=idempotency_key,
                answer_id=event.answer_id,
                user_id=event.user_id,
                status=EVENT_STATUS_COMPLETED,
                response_xp=replay_user.xp,
                response_level=replay_user.level,
            )

        return XpAwardResult(
            user=replay_user,
            is_duplicate=True,
            status=event.status,
        )

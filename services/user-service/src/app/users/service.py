from __future__ import annotations

import sqlite3

from app.config import Settings
from app.security import create_access_token, hash_password, verify_password
from app.users.models import User
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


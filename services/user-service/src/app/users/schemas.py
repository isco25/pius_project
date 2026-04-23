from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

from app.users.models import User


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserCredentials(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("Invalid email format")
        return normalized


class RegisterRequest(UserCredentials):
    pass


class LoginRequest(UserCredentials):
    pass


class UserResponse(BaseModel):
    id: int
    email: str

    @classmethod
    def from_model(cls, user: User) -> "UserResponse":
        return cls(id=user.id, email=user.email)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


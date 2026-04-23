from __future__ import annotations

from dataclasses import dataclass

EVENT_STATUS_PENDING = "pending"
EVENT_STATUS_COMPLETED = "completed"
EVENT_STATUS_FAILED = "failed"


@dataclass(frozen=True, slots=True)
class User:
    id: int
    email: str
    password_hash: str
    xp: int
    level: int


@dataclass(frozen=True, slots=True)
class ProcessedEvent:
    id: int
    answer_id: int
    user_id: int
    xp_awarded: int
    status: str
    result_xp: int | None
    result_level: int | None
    created_at: str


@dataclass(frozen=True, slots=True)
class IdempotencyKeyRecord:
    id: int
    key: str
    answer_id: int
    user_id: int
    status: str
    response_xp: int | None
    response_level: int | None
    created_at: str


@dataclass(frozen=True, slots=True)
class EventCreationResult:
    created: bool
    event: ProcessedEvent | None = None
    idempotency_record: IdempotencyKeyRecord | None = None


@dataclass(frozen=True, slots=True)
class XpAwardResult:
    user: User
    is_duplicate: bool
    status: str

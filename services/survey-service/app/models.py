from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Survey(Base):
    __tablename__ = "surveys"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")

    answers: Mapped[list["Answer"]] = relationship(
        back_populates="survey",
        cascade="all, delete-orphan",
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    survey_id: Mapped[int] = mapped_column(
        ForeignKey("surveys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    answers: Mapped[dict] = mapped_column(JSON, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    survey: Mapped["Survey"] = relationship(back_populates="answers")

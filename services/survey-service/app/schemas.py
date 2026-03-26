from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SurveyStatus = Literal["draft", "active", "closed"]


class SurveyBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    status: SurveyStatus = "draft"


class SurveyCreate(SurveyBase):
    pass


class SurveyUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: SurveyStatus | None = None


class SurveyRead(SurveyBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class AnswerCreate(BaseModel):
    survey_id: int
    answers: dict[str, Any]


class AnswerRead(BaseModel):
    id: int
    survey_id: int
    answers: dict[str, Any]
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnswerCountRead(BaseModel):
    survey_id: int
    answers_count: int

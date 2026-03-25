from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.clients.survey_client import fetch_answer_count

router = APIRouter(prefix="/analytics", tags=["Аналитика"])


class BasicAnalyticsResponse(BaseModel):
    survey_id: int
    answers_count: int


@router.get(
    "/surveys/{survey_id}/basic",
    response_model=BasicAnalyticsResponse,
    summary="Базовая статистика",
    description="Возвращает количество ответов по опросу.",
)
def get_basic_analytics(survey_id: int) -> BasicAnalyticsResponse:
    answers_count = fetch_answer_count(survey_id)
    return BasicAnalyticsResponse(survey_id=survey_id, answers_count=answers_count)

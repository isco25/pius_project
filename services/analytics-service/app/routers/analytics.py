from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.clients.survey_client import fetch_answer_count, fetch_user_surveys

router = APIRouter(prefix="/analytics", tags=["Аналитика"])


class BasicAnalyticsResponse(BaseModel):
    survey_id: int
    answers_count: int


class UserStatisticsResponse(BaseModel):
    user_id: int
    total_surveys: int
    total_answers: int
    surveys: List[BasicAnalyticsResponse]


@router.get(
    "/surveys/{survey_id}/basic",
    response_model=BasicAnalyticsResponse,
    summary="Базовая статистика",
    description="Возвращает количество ответов по опросу.",
)
def get_basic_analytics(survey_id: int) -> BasicAnalyticsResponse:
    answers_count = fetch_answer_count(survey_id)
    return BasicAnalyticsResponse(survey_id=survey_id, answers_count=answers_count)


@router.get(
    "/users/{user_id}/statistics",
    response_model=UserStatisticsResponse,
    summary="Статистика пользователя",
    description="Возвращает статистику по всем опросам пользователя.",
)
def get_user_statistics(user_id: int) -> UserStatisticsResponse:
    """
    Получение статистики по всем опросам пользователя.
    
    - **user_id**: идентификатор пользователя
    """
    # Получаем список опросов пользователя из сервиса опросов
    surveys = fetch_user_surveys(user_id)
    
    if surveys is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or has no surveys"
        )
    
    total_answers = 0
    surveys_stats = []
    
    for survey in surveys:
        survey_id = survey["id"]
        answers_count = fetch_answer_count(survey_id)
        total_answers += answers_count
        surveys_stats.append(
            BasicAnalyticsResponse(
                survey_id=survey_id,
                answers_count=answers_count
            )
        )
    
    return UserStatisticsResponse(
        user_id=user_id,
        total_surveys=len(surveys),
        total_answers=total_answers,
        surveys=surveys_stats
    )
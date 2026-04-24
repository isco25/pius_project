from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class BasicAnalyticsResponse(BaseModel):
    survey_id: int
    answers_count: int


class UserStatisticsResponse(BaseModel):
    user_id: int
    total_surveys: int
    total_answers: int
    surveys: List[BasicAnalyticsResponse]


class AnswerCreatedEventRequest(BaseModel):
    user_id: int
    answer_id: str = Field(min_length=1)
    question_id: int
    survey_id: int


class AwardedAchievementResponse(BaseModel):
    id: int
    name: str
    description: str
    awarded_at: str


class AnswerCreatedEventResponse(BaseModel):
    status: str
    answer_id: str
    survey_id: int
    question_id: int
    answer_count: int
    awarded_achievements: List[AwardedAchievementResponse]


class DetailedQuestionAnalyticsResponse(BaseModel):
    question_id: int
    answer_count: int
    percentage: float


class DetailedSurveyAnalyticsResponse(BaseModel):
    survey_id: int
    total_answers: int
    questions: List[DetailedQuestionAnalyticsResponse]


class UserAchievementResponse(BaseModel):
    id: int
    name: str
    description: str
    awarded_at: str


class UserAchievementsListResponse(BaseModel):
    user_id: int
    achievements: List[UserAchievementResponse]

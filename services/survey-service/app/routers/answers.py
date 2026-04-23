from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Answer, Survey
from app.schemas import AnswerCreate, AnswerRead

router = APIRouter(prefix="/answers", tags=["Ответы"])


@router.post(
    "",
    response_model=AnswerRead,
    responses={404: {"description": "Survey not found"}},
    status_code=status.HTTP_201_CREATED,
    summary="Сохранить ответ",
    description="Сохраняет ответ на опрос.",
)
def create_answer(payload: AnswerCreate, db: Session = Depends(get_db)) -> Answer:
    survey = db.get(Survey, payload.survey_id)
    if survey is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    answer = Answer(**payload.model_dump())
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer



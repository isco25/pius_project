from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException, status

SURVEY_SERVICE_URL = os.getenv("SURVEY_SERVICE_URL", "http://localhost:8002")  # Обратите внимание на порт


def fetch_answer_count(survey_id: int) -> int:
    """Получение количества ответов по опросу"""
    url = f"{SURVEY_SERVICE_URL}/surveys/{survey_id}/answers/count"
    try:
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Survey service returned an error",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Survey service is unavailable",
        ) from exc

    payload = response.json()
    return int(payload["answers_count"])


def fetch_user_surveys(user_id: int) -> Optional[List[Dict[str, Any]]]:
    """
    Получение списка опросов пользователя.
    
    Args:
        user_id: идентификатор пользователя
        
    Returns:
        Список опросов пользователя или None, если пользователь не найден
    """
    url = f"{SURVEY_SERVICE_URL}/users/{user_id}/surveys"
    
    try:
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == status.HTTP_404_NOT_FOUND:
            return None
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Survey service returned an error",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Survey service is unavailable",
        ) from exc
    
    return response.json()


def fetch_all_surveys_stats() -> Dict[str, Any]:
    """Получение общей статистики по всем опросам"""
    url = f"{SURVEY_SERVICE_URL}/surveys/statistics"
    
    try:
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Survey service is unavailable",
        ) from exc
    
    return response.json()


def check_survey_service_health() -> bool:
    """Проверка доступности Survey Service"""
    url = f"{SURVEY_SERVICE_URL}/health"
    
    try:
        response = httpx.get(url, timeout=2.0)
        return response.status_code == 200
    except httpx.HTTPError:
        return False
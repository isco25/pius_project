from __future__ import annotations

import os

import httpx
from fastapi import HTTPException, status

SURVEY_SERVICE_URL = os.getenv("SURVEY_SERVICE_URL", "http://localhost:8001")


def fetch_answer_count(survey_id: int) -> int:
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

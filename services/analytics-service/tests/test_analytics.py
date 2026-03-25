from __future__ import annotations

from fastapi import HTTPException
from fastapi.testclient import TestClient

import app.main as analytics_main
import app.routers.analytics as analytics_router


def test_basic_analytics_returns_count(monkeypatch) -> None:
    def fake_fetch(_: int) -> int:
        return 7

    monkeypatch.setattr(analytics_router, "fetch_answer_count", fake_fetch)
    client = TestClient(analytics_main.app)

    response = client.get("/analytics/surveys/1/basic")

    assert response.status_code == 200
    assert response.json() == {"survey_id": 1, "answers_count": 7}


def test_basic_analytics_propagates_not_found(monkeypatch) -> None:
    def fake_fetch(_: int) -> int:
        raise HTTPException(status_code=404, detail="Survey not found")

    monkeypatch.setattr(analytics_router, "fetch_answer_count", fake_fetch)
    client = TestClient(analytics_main.app)

    response = client.get("/analytics/surveys/999/basic")

    assert response.status_code == 404
    assert response.json() == {"detail": "Survey not found"}


def test_basic_analytics_propagates_upstream_error(monkeypatch) -> None:
    def fake_fetch(_: int) -> int:
        raise HTTPException(status_code=502, detail="Survey service is unavailable")

    monkeypatch.setattr(analytics_router, "fetch_answer_count", fake_fetch)
    client = TestClient(analytics_main.app)

    response = client.get("/analytics/surveys/1/basic")

    assert response.status_code == 502
    assert response.json() == {"detail": "Survey service is unavailable"}

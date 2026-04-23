from __future__ import annotations

from fastapi.testclient import TestClient


def create_sample_survey(client: TestClient) -> int:
    response = client.post(
        "/surveys",
        json={
            "title": "Python Survey",
            "description": "Basic questionnaire",
            "status": "draft",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_and_get_survey(client: TestClient) -> None:
    survey_id = create_sample_survey(client)

    response = client.get(f"/surveys/{survey_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == survey_id
    assert body["title"] == "Python Survey"


def test_list_surveys(client: TestClient) -> None:
    create_sample_survey(client)

    response = client.get("/surveys")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Python Survey"


def test_update_survey(client: TestClient) -> None:
    survey_id = create_sample_survey(client)

    response = client.put(
        f"/surveys/{survey_id}",
        json={"title": "Updated Survey", "status": "active"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Updated Survey"
    assert body["status"] == "active"


def test_delete_survey(client: TestClient) -> None:
    survey_id = create_sample_survey(client)

    delete_response = client.delete(f"/surveys/{survey_id}")
    get_response = client.get(f"/surveys/{survey_id}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_get_missing_survey_returns_404(client: TestClient) -> None:
    response = client.get("/surveys/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Survey not found"


def test_create_answer_and_count_answers(client: TestClient) -> None:
    survey_id = create_sample_survey(client)

    answer_response = client.post(
        "/answers",
        json={
            "survey_id": survey_id,
            "answers": [
                {"name": "q1", "value": "yes"},
                {"name": "q2", "value": "python"},
            ],
        },
    )
    count_response = client.get(f"/surveys/{survey_id}/answers/count")

    assert answer_response.status_code == 201
    assert answer_response.json()["survey_id"] == survey_id
    assert count_response.status_code == 200
    assert count_response.json()["answers_count"] == 1

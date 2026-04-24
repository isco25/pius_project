# Analytics Service

Analytics Service aggregates survey answer events, stores per-question statistics,
exports analytics, and awards user achievements.

## Stack

- Python 3.11+
- FastAPI
- SQLite
- Alembic
- HTTPX
- unittest + TestClient

## What Is Implemented

- `POST /internal/events/answer-created`
  Processes `answer.created` events and updates local analytics.
- `GET /analytics/surveys/{survey_id}/basic`
  Keeps the existing upstream-based basic analytics endpoint.
- `GET /analytics/surveys/{survey_id}/detailed`
  Returns detailed per-question survey statistics from the local analytics DB.
- `GET /analytics/surveys/{survey_id}/export?format=csv`
  Exports detailed survey statistics in CSV format.
- `GET /users/{user_id}/achievements`
  Returns user achievements awarded from processed events.

## Environment Variables

```env
SURVEY_SERVICE_URL=http://localhost:8002
DATABASE_URL=sqlite:///./data/analytics.db
INTERNAL_API_KEY=change-me
```

Notes:

- `DATABASE_URL` currently expects a SQLite path.
- Internal event requests must send either `X-Internal-Token` or
  `Authorization: Bearer <token>`.
- `Idempotency-Key` is supported for safe retries and returns the stored response
  on replay.

## Local Run

```bash
cd services/analytics-service
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8003
```

## Migrations

Initialize or upgrade the schema:

```bash
cd services/analytics-service
python -m pip install -r requirements.txt
alembic upgrade head
```

The service also creates the latest schema on startup for local development and
tests, while Alembic revisions are included for managed environments.

## Data Model

The service uses these core tables:

- `question_stats`
  Per-survey, per-question answer counters.
- `processed_events`
  Deduplication store and operation state for processed answer events.
- `idempotency_keys`
  Saved request hashes and stored responses for replay-safe retries.
- `achievements`
  Predefined achievement catalog.
- `user_achievements`
  Award history per user.

Predefined achievements:

- `Первый ответ`
- `10 ответов`
- `100 ответов`
- `Мастер опросов`

## API Examples

Process an internal event:

```bash
curl -X POST "http://localhost:8003/internal/events/answer-created" \
  -H "Content-Type: application/json" \
  -H "X-Internal-Token: change-me" \
  -H "Idempotency-Key: event-answer-1001" \
  -d '{
    "user_id": 7,
    "answer_id": "1001",
    "question_id": 15,
    "survey_id": 3
  }'
```

Fetch detailed analytics:

```bash
curl "http://localhost:8003/analytics/surveys/3/detailed"
```

Export CSV:

```bash
curl -OJ "http://localhost:8003/analytics/surveys/3/export?format=csv"
```

Fetch user achievements:

```bash
curl "http://localhost:8003/users/7/achievements"
```

## Event Processing Guarantees

- Internal token validation protects the receiver.
- `answer_id` is used as the business key.
- Duplicate `answer_id` values are not processed twice.
- Operation states are stored as `pending`, `completed`, or `failed`.
- Replayed `Idempotency-Key` requests return the saved response.

## Testing

Install development dependencies:

```bash
cd services/analytics-service
python -m pip install -r requirements-dev.txt
```

Run the unittest suite directly:

```bash
python -m unittest discover -s tests -p "test_analytics.py" -v
```

If `pytest` is installed, this also works:

```bash
python -m pytest
```

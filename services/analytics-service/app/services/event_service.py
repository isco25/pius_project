from __future__ import annotations

import json
import sqlite3
from hashlib import sha256
from typing import Any

from fastapi import HTTPException, status

from app.db import get_connection, utcnow
from app.schemas import AnswerCreatedEventRequest
from app.services.achievement_service import award_achievements
from app.services.analytics_service import increment_question_stat


def process_answer_created_event(
    payload: AnswerCreatedEventRequest,
    idempotency_key: str | None,
) -> tuple[int, dict[str, Any]]:
    request_hash = _build_request_hash(payload)

    with get_connection() as connection:
        try:
            connection.execute("BEGIN")

            if idempotency_key:
                replayed_response = _get_idempotency_replay(
                    connection,
                    idempotency_key,
                    request_hash,
                )
                if replayed_response is not None:
                    connection.commit()
                    return replayed_response

            try:
                _insert_pending_event(connection, payload)
            except sqlite3.IntegrityError:
                existing_event = connection.execute(
                    """
                    SELECT status, response_status_code, response_body, error_message
                    FROM processed_events
                    WHERE answer_id = ?
                    """,
                    (payload.answer_id,),
                ).fetchone()
                if existing_event is None:
                    raise

                response_status, response_body = _load_stored_response(existing_event)
                if idempotency_key:
                    _upsert_idempotency_record(
                        connection=connection,
                        idempotency_key=idempotency_key,
                        request_hash=request_hash,
                        answer_id=payload.answer_id,
                        operation_status=str(existing_event["status"]),
                        response_status=response_status,
                        response_body=response_body,
                    )

                connection.commit()
                return response_status, response_body

            if idempotency_key:
                _upsert_idempotency_record(
                    connection=connection,
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    answer_id=payload.answer_id,
                    operation_status="pending",
                    response_status=status.HTTP_202_ACCEPTED,
                    response_body={"detail": "Request is being processed"},
                )

            answer_count = increment_question_stat(
                connection,
                survey_id=payload.survey_id,
                question_id=payload.question_id,
            )
            awarded_achievements = award_achievements(
                connection,
                user_id=payload.user_id,
                answer_id=payload.answer_id,
            )

            response_body = {
                "status": "processed",
                "answer_id": payload.answer_id,
                "survey_id": payload.survey_id,
                "question_id": payload.question_id,
                "answer_count": answer_count,
                "awarded_achievements": awarded_achievements,
            }

            _mark_event_completed(connection, payload.answer_id, response_body)

            if idempotency_key:
                _upsert_idempotency_record(
                    connection=connection,
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    answer_id=payload.answer_id,
                    operation_status="completed",
                    response_status=status.HTTP_200_OK,
                    response_body=response_body,
                )

            connection.commit()
            return status.HTTP_200_OK, response_body
        except HTTPException:
            connection.rollback()
            raise
        except Exception as exc:
            connection.rollback()
            failure_body = {"detail": "Failed to process event"}
            _persist_failed_operation(
                payload=payload,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                response_body=failure_body,
                error_message=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process event",
            ) from exc


def _build_request_hash(payload: AnswerCreatedEventRequest) -> str:
    encoded_payload = json.dumps(
        payload.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded_payload.encode("utf-8")).hexdigest()


def _get_idempotency_replay(
    connection: sqlite3.Connection,
    idempotency_key: str,
    request_hash: str,
) -> tuple[int, dict[str, Any]] | None:
    row = connection.execute(
        """
        SELECT request_hash, status, response_status_code, response_body
        FROM idempotency_keys
        WHERE key = ?
        """,
        (idempotency_key,),
    ).fetchone()

    if row is None:
        return None

    if str(row["request_hash"]) != request_hash:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency-Key cannot be reused with a different payload",
        )

    if str(row["status"]) == "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Request with this Idempotency-Key is already being processed",
        )

    return _load_stored_response(row)


def _insert_pending_event(
    connection: sqlite3.Connection,
    payload: AnswerCreatedEventRequest,
) -> None:
    timestamp = utcnow()
    connection.execute(
        """
        INSERT INTO processed_events (
            answer_id,
            user_id,
            question_id,
            survey_id,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, 'pending', ?, ?)
        """,
        (
            payload.answer_id,
            payload.user_id,
            payload.question_id,
            payload.survey_id,
            timestamp,
            timestamp,
        ),
    )


def _mark_event_completed(
    connection: sqlite3.Connection,
    answer_id: str,
    response_body: dict[str, Any],
) -> None:
    connection.execute(
        """
        UPDATE processed_events
        SET
            status = 'completed',
            response_status_code = ?,
            response_body = ?,
            error_message = NULL,
            updated_at = ?
        WHERE answer_id = ?
        """,
        (
            status.HTTP_200_OK,
            _dump_json(response_body),
            utcnow(),
            answer_id,
        ),
    )


def _persist_failed_operation(
    *,
    payload: AnswerCreatedEventRequest,
    idempotency_key: str | None,
    request_hash: str,
    response_status: int,
    response_body: dict[str, Any],
    error_message: str,
) -> None:
    with get_connection() as connection:
        connection.execute("BEGIN")
        timestamp = utcnow()
        serialized_body = _dump_json(response_body)

        connection.execute(
            """
            INSERT INTO processed_events (
                answer_id,
                user_id,
                question_id,
                survey_id,
                status,
                response_status_code,
                response_body,
                error_message,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, 'failed', ?, ?, ?, ?, ?)
            ON CONFLICT(answer_id) DO UPDATE SET
                user_id = excluded.user_id,
                question_id = excluded.question_id,
                survey_id = excluded.survey_id,
                status = excluded.status,
                response_status_code = excluded.response_status_code,
                response_body = excluded.response_body,
                error_message = excluded.error_message,
                updated_at = excluded.updated_at
            """,
            (
                payload.answer_id,
                payload.user_id,
                payload.question_id,
                payload.survey_id,
                response_status,
                serialized_body,
                error_message,
                timestamp,
                timestamp,
            ),
        )

        if idempotency_key:
            _upsert_idempotency_record(
                connection=connection,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                answer_id=payload.answer_id,
                operation_status="failed",
                response_status=response_status,
                response_body=response_body,
            )

        connection.commit()


def _upsert_idempotency_record(
    *,
    connection: sqlite3.Connection,
    idempotency_key: str,
    request_hash: str,
    answer_id: str,
    operation_status: str,
    response_status: int,
    response_body: dict[str, Any],
) -> None:
    timestamp = utcnow()
    connection.execute(
        """
        INSERT INTO idempotency_keys (
            key,
            request_hash,
            answer_id,
            status,
            response_status_code,
            response_body,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            request_hash = excluded.request_hash,
            answer_id = excluded.answer_id,
            status = excluded.status,
            response_status_code = excluded.response_status_code,
            response_body = excluded.response_body,
            updated_at = excluded.updated_at
        """,
        (
            idempotency_key,
            request_hash,
            answer_id,
            operation_status,
            response_status,
            _dump_json(response_body),
            timestamp,
            timestamp,
        ),
    )


def _load_stored_response(row: sqlite3.Row) -> tuple[int, dict[str, Any]]:
    stored_status = str(row["status"])

    if row["response_body"]:
        return int(row["response_status_code"] or status.HTTP_200_OK), json.loads(
            str(row["response_body"])
        )

    if stored_status == "pending":
        return status.HTTP_409_CONFLICT, {"detail": "Event is already being processed"}

    return int(
        row["response_status_code"] or status.HTTP_500_INTERNAL_SERVER_ERROR
    ), {
        "detail": "Failed to process event",
    }


def _dump_json(value: dict[str, Any]) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )

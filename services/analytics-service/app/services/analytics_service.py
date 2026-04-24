from __future__ import annotations

import sqlite3
from typing import Any


def increment_question_stat(
    connection: sqlite3.Connection,
    survey_id: int,
    question_id: int,
) -> int:
    connection.execute(
        """
        INSERT INTO question_stats (survey_id, question_id, answer_count)
        VALUES (?, ?, 1)
        ON CONFLICT(survey_id, question_id) DO UPDATE SET
            answer_count = answer_count + 1
        """,
        (survey_id, question_id),
    )

    row = connection.execute(
        """
        SELECT answer_count
        FROM question_stats
        WHERE survey_id = ? AND question_id = ?
        """,
        (survey_id, question_id),
    ).fetchone()

    return int(row["answer_count"])


def get_detailed_survey_stats(
    connection: sqlite3.Connection,
    survey_id: int,
) -> dict[str, Any]:
    rows = connection.execute(
        """
        SELECT question_id, answer_count
        FROM question_stats
        WHERE survey_id = ?
        ORDER BY question_id
        """,
        (survey_id,),
    ).fetchall()

    total_answers = sum(int(row["answer_count"]) for row in rows)
    questions = []

    for row in rows:
        answer_count = int(row["answer_count"])
        percentage = round((answer_count / total_answers) * 100, 2) if total_answers else 0.0
        questions.append(
            {
                "question_id": int(row["question_id"]),
                "answer_count": answer_count,
                "percentage": percentage,
            }
        )

    return {
        "survey_id": survey_id,
        "total_answers": total_answers,
        "questions": questions,
    }

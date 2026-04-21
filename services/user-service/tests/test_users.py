from __future__ import annotations

import gc
import os
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from fastapi.testclient import TestClient

from app.application import create_app


class UserApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["DATABASE_URL"] = str(Path(self.temp_dir.name) / "test.db")
        os.environ["JWT_SECRET"] = "test-secret"
        os.environ["JWT_EXPIRATION_MINUTES"] = "30"
        os.environ["INTERNAL_API_KEY"] = "internal-test-key"
        self.client = TestClient(create_app())

    def tearDown(self) -> None:
        self.client.close()
        os.environ.pop("DATABASE_URL", None)
        os.environ.pop("JWT_SECRET", None)
        os.environ.pop("JWT_EXPIRATION_MINUTES", None)
        os.environ.pop("INTERNAL_API_KEY", None)
        gc.collect()
        time.sleep(0.1)
        try:
            self.temp_dir.cleanup()
        except (PermissionError, NotADirectoryError):
            pass

    def test_register_user_successfully(self) -> None:
        response = self.client.post(
            "/register",
            json={"email": "alice@example.com", "password": "StrongPass123"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {"id": 1, "email": "alice@example.com"},
        )

    def test_register_rejects_duplicate_email(self) -> None:
        self.register_user()

        response = self.client.post(
            "/register",
            json={"email": "alice@example.com", "password": "StrongPass123"},
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"], "User with this email already exists")

    def test_login_returns_jwt_token(self) -> None:
        self.register_user()

        response = self.client.post(
            "/login",
            json={"email": "alice@example.com", "password": "StrongPass123"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["token_type"], "bearer")
        self.assertTrue(body["access_token"])

    def test_login_rejects_invalid_password(self) -> None:
        self.register_user()

        response = self.client.post(
            "/login",
            json={"email": "alice@example.com", "password": "WrongPass123"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid email or password")

    def test_get_user_requires_jwt_token(self) -> None:
        created_user = self.register_user()

        response = self.client.get(f"/users/{created_user['id']}")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Authentication required")

    def test_get_user_returns_user_for_valid_token(self) -> None:
        created_user = self.register_user()
        access_token = self.login_user()["access_token"]

        response = self.client.get(
            f"/users/{created_user['id']}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"id": created_user["id"], "email": created_user["email"]},
        )

    def test_get_user_returns_not_found_for_unknown_id(self) -> None:
        self.register_user()
        access_token = self.login_user()["access_token"]

        response = self.client.get(
            "/users/999",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "User not found")

    def test_get_user_stats_returns_initial_xp_and_level(self) -> None:
        created_user = self.register_user()

        response = self.client.get(f"/users/{created_user['id']}/stats")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": created_user["id"],
                "email": created_user["email"],
                "xp": 0,
                "level": 0,
            },
        )

    def test_answer_created_event_adds_xp_and_increases_level(self) -> None:
        created_user = self.register_user()

        response = None
        for answer_id in range(1, 21):
            response = self.client.post(
                "/internal/events/answer-created",
                json={
                    "user_id": created_user["id"],
                    "answer_id": answer_id,
                    "question_id": 10 + answer_id,
                    "survey_id": 100 + answer_id,
                },
                headers=self.internal_headers(),
            )

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": created_user["id"],
                "email": created_user["email"],
                "xp": 100,
                "level": 1,
            },
        )

    def test_answer_created_event_returns_404_for_unknown_user(self) -> None:
        response = self.client.post(
            "/internal/events/answer-created",
            json={"user_id": 999, "answer_id": 1, "question_id": 2, "survey_id": 3},
            headers=self.internal_headers(),
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "User not found")

    def test_answer_created_event_requires_internal_api_key(self) -> None:
        created_user = self.register_user()

        response = self.client.post(
            "/internal/events/answer-created",
            json={
                "user_id": created_user["id"],
                "answer_id": 1,
                "question_id": 2,
                "survey_id": 3,
            },
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid internal API key")

    def test_answer_created_event_reuses_answer_id_without_double_xp(self) -> None:
        created_user = self.register_user()

        first_response = self.client.post(
            "/internal/events/answer-created",
            json={
                "user_id": created_user["id"],
                "answer_id": 77,
                "question_id": 7,
                "survey_id": 17,
            },
            headers=self.internal_headers(),
        )
        second_response = self.client.post(
            "/internal/events/answer-created",
            json={
                "user_id": created_user["id"],
                "answer_id": 77,
                "question_id": 7,
                "survey_id": 17,
            },
            headers=self.internal_headers(idempotency_key="dedup-key-77"),
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(first_response.json()["xp"], 5)
        self.assertEqual(second_response.json()["xp"], 5)

        stats_response = self.client.get(f"/users/{created_user['id']}/stats")
        self.assertEqual(stats_response.status_code, 200)
        self.assertEqual(stats_response.json()["xp"], 5)

    def test_answer_created_event_reuses_idempotency_key_without_double_xp(self) -> None:
        created_user = self.register_user()
        idempotency_key = "123e4567-e89b-12d3-a456-426614174000"

        first_response = self.client.post(
            "/internal/events/answer-created",
            json={
                "user_id": created_user["id"],
                "answer_id": 101,
                "question_id": 11,
                "survey_id": 21,
            },
            headers=self.internal_headers(idempotency_key=idempotency_key),
        )
        next_response = self.client.post(
            "/internal/events/answer-created",
            json={
                "user_id": created_user["id"],
                "answer_id": 202,
                "question_id": 22,
                "survey_id": 32,
            },
            headers=self.internal_headers(),
        )
        replay_response = self.client.post(
            "/internal/events/answer-created",
            json={
                "user_id": created_user["id"],
                "answer_id": 999,
                "question_id": 99,
                "survey_id": 199,
            },
            headers=self.internal_headers(idempotency_key=idempotency_key),
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(next_response.status_code, 200)
        self.assertEqual(replay_response.status_code, 200)
        self.assertEqual(first_response.json()["xp"], 5)
        self.assertEqual(next_response.json()["xp"], 10)
        self.assertEqual(replay_response.json()["xp"], 5)

        stats_response = self.client.get(f"/users/{created_user['id']}/stats")
        self.assertEqual(stats_response.status_code, 200)
        self.assertEqual(stats_response.json()["xp"], 10)

    def test_answer_created_event_marks_failed_status_for_unknown_user(self) -> None:
        response = self.client.post(
            "/internal/events/answer-created",
            json={"user_id": 404, "answer_id": 808, "question_id": 9, "survey_id": 10},
            headers=self.internal_headers(idempotency_key="failed-event-key"),
        )

        self.assertEqual(response.status_code, 404)

        with sqlite3.connect(Path(self.temp_dir.name) / "test.db") as connection:
            event_row = connection.execute(
                "SELECT status FROM processed_events WHERE answer_id = ?",
                (808,),
            ).fetchone()
            idempotency_row = connection.execute(
                'SELECT status FROM idempotency_keys WHERE "key" = ?',
                ("failed-event-key",),
            ).fetchone()

        self.assertIsNotNone(event_row)
        self.assertEqual(event_row[0], "failed")
        self.assertIsNotNone(idempotency_row)
        self.assertEqual(idempotency_row[0], "failed")

    def test_leaderboard_returns_users_sorted_by_xp(self) -> None:
        alice = self.register_user(email="alice@example.com")
        bob = self.register_user(email="bob@example.com")

        self.add_xp_events(alice["id"], count=2, start_answer_id=1)
        self.add_xp_events(bob["id"], count=4, start_answer_id=101)

        response = self.client.get("/leaderboard?limit=10&offset=0")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {"id": bob["id"], "email": bob["email"], "xp": 20, "level": 0},
                {"id": alice["id"], "email": alice["email"], "xp": 10, "level": 0},
            ],
        )

    def register_user(
        self,
        email: str = "alice@example.com",
        password: str = "StrongPass123",
    ) -> dict[str, object]:
        response = self.client.post(
            "/register",
            json={"email": email, "password": password},
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    def login_user(
        self,
        email: str = "alice@example.com",
        password: str = "StrongPass123",
    ) -> dict[str, str]:
        response = self.client.post(
            "/login",
            json={"email": email, "password": password},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def add_xp_events(self, user_id: object, count: int, start_answer_id: int = 1) -> None:
        for answer_id in range(start_answer_id, start_answer_id + count):
            response = self.client.post(
                "/internal/events/answer-created",
                json={
                    "user_id": user_id,
                    "answer_id": answer_id,
                    "question_id": 100 + answer_id,
                    "survey_id": 200 + answer_id,
                },
                headers=self.internal_headers(),
            )
            self.assertEqual(response.status_code, 200)

    def internal_headers(self, idempotency_key: str | None = None) -> dict[str, str]:
        headers = {"X-Internal-Token": "internal-test-key"}
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        return headers


class LegacyMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_file.close()
        self.database_path = Path(temp_file.name)
        os.environ["DATABASE_URL"] = str(self.database_path)
        os.environ["JWT_SECRET"] = "test-secret"
        os.environ["JWT_EXPIRATION_MINUTES"] = "30"
        os.environ["INTERNAL_API_KEY"] = "internal-test-key"

        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                ("legacy@example.com", "hashed-password"),
            )
            connection.commit()

    def tearDown(self) -> None:
        os.environ.pop("DATABASE_URL", None)
        os.environ.pop("JWT_SECRET", None)
        os.environ.pop("JWT_EXPIRATION_MINUTES", None)
        os.environ.pop("INTERNAL_API_KEY", None)
        if self.database_path.exists():
            gc.collect()
            time.sleep(0.1)
            try:
                self.database_path.unlink()
            except PermissionError:
                pass

    def test_create_app_upgrades_legacy_database(self) -> None:
        with TestClient(create_app()) as client:
            response = client.get("/users/1/stats")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"id": 1, "email": "legacy@example.com", "xp": 0, "level": 0},
        )

        with sqlite3.connect(self.database_path) as connection:
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(users)").fetchall()
            }
            version_row = connection.execute(
                "SELECT version_num FROM alembic_version"
            ).fetchone()

        self.assertIn("xp", columns)
        self.assertIn("level", columns)
        self.assertIsNotNone(version_row)
        self.assertEqual(version_row[0], "0003_create_event_deduplication_tables")


class UserRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["DATABASE_URL"] = str(Path(self.temp_dir.name) / "test.db")
        os.environ["JWT_SECRET"] = "test-secret"
        os.environ["JWT_EXPIRATION_MINUTES"] = "30"
        os.environ["INTERNAL_API_KEY"] = "internal-test-key"
        self.app = create_app()
        self.repository = self.app.state.user_repository

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        os.environ.pop("DATABASE_URL", None)
        os.environ.pop("JWT_SECRET", None)
        os.environ.pop("JWT_EXPIRATION_MINUTES", None)
        os.environ.pop("INTERNAL_API_KEY", None)

    def test_create_idempotent_event_handles_unique_answer_conflict(self) -> None:
        user = self.repository.create(
            email="repo@example.com",
            password_hash="hashed-password",
        )

        first_attempt = self.repository.create_idempotent_event(
            answer_id=1234,
            user_id=user.id,
            idempotency_key="repo-conflict-key",
        )
        second_attempt = self.repository.create_idempotent_event(
            answer_id=1234,
            user_id=user.id,
            idempotency_key="repo-conflict-key-2",
        )

        self.assertTrue(first_attempt.created)
        self.assertFalse(second_attempt.created)
        self.assertIsNotNone(second_attempt.event)
        self.assertEqual(second_attempt.event.answer_id, 1234)


if __name__ == "__main__":
    unittest.main()

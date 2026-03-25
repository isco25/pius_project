from __future__ import annotations

from pathlib import Path
import os
import sys
import tempfile
import unittest

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
        self.client = TestClient(create_app())

    def tearDown(self) -> None:
        self.client.close()
        self.temp_dir.cleanup()
        os.environ.pop("DATABASE_URL", None)
        os.environ.pop("JWT_SECRET", None)
        os.environ.pop("JWT_EXPIRATION_MINUTES", None)

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

    def register_user(self) -> dict[str, object]:
        response = self.client.post(
            "/register",
            json={"email": "alice@example.com", "password": "StrongPass123"},
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    def login_user(self) -> dict[str, str]:
        response = self.client.post(
            "/login",
            json={"email": "alice@example.com", "password": "StrongPass123"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()


if __name__ == "__main__":
    unittest.main()

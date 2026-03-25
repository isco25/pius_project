from __future__ import annotations

from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json
import secrets


class TokenError(Exception):
    """Raised when a JWT is invalid or expired."""


def hash_password(password: str, iterations: int = 390_000) -> str:
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        iterations,
    )
    return f"pbkdf2_sha256${iterations}${salt}${password_hash.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, iterations_raw, salt, expected_hash = stored_hash.split("$", maxsplit=3)
    except ValueError:
        return False

    if scheme != "pbkdf2_sha256":
        return False

    candidate_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        int(iterations_raw),
    ).hex()
    return hmac.compare_digest(candidate_hash, expected_hash)


def create_access_token(
    subject: int,
    secret: str,
    expires_minutes: int,
    algorithm: str = "HS256",
) -> str:
    if algorithm != "HS256":
        raise ValueError("Only HS256 is supported")

    now = datetime.now(UTC)
    payload = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return _encode_token(payload, secret)


def decode_access_token(token: str, secret: str, algorithm: str = "HS256") -> dict[str, object]:
    if algorithm != "HS256":
        raise TokenError("Unsupported JWT algorithm")

    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
    except ValueError as error:
        raise TokenError("Malformed token") from error

    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    expected_signature = _sign(signing_input, secret)

    if not hmac.compare_digest(expected_signature, encoded_signature):
        raise TokenError("Invalid token signature")

    try:
        header = json.loads(_urlsafe_b64decode(encoded_header))
        payload = json.loads(_urlsafe_b64decode(encoded_payload))
    except (json.JSONDecodeError, ValueError) as error:
        raise TokenError("Malformed token payload") from error

    if header.get("alg") != "HS256" or header.get("typ") != "JWT":
        raise TokenError("Invalid token header")

    if int(payload.get("exp", 0)) < int(datetime.now(UTC).timestamp()):
        raise TokenError("Token has expired")

    return payload


def _encode_token(payload: dict[str, object], secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _urlsafe_b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = _urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = _sign(signing_input, secret)
    return f"{encoded_header}.{encoded_payload}.{signature}"


def _sign(message: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    return _urlsafe_b64encode(digest)


def _urlsafe_b64encode(value: bytes) -> str:
    return urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _urlsafe_b64decode(value: str) -> str:
    padding = "=" * (-len(value) % 4)
    return urlsafe_b64decode(f"{value}{padding}".encode("utf-8")).decode("utf-8")


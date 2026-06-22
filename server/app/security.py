from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from server.app.infrastructure.settings import get_settings

PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 260_000
TOKEN_ALGORITHM = "HS256"


class AuthError(ValueError):
    pass


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return f"{PASSWORD_ALGORITHM}${PASSWORD_ITERATIONS}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected = password_hash.split("$", 3)
        if algorithm != PASSWORD_ALGORITHM:
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), _b64decode(salt), int(iterations))
        return hmac.compare_digest(_b64encode(digest), expected)
    except (ValueError, TypeError):
        return False


def _sign(message: str) -> str:
    secret = get_settings().auth_secret_key.encode("utf-8")
    return _b64encode(hmac.new(secret, message.encode("ascii"), hashlib.sha256).digest())


def create_access_token(
    *,
    subject: str,
    role: str,
    username: str,
    display_name: str,
    password_version: int,
    expires_minutes: int | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=expires_minutes or settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "username": username,
        "display_name": display_name,
        "password_version": password_version,
        "jti": secrets.token_urlsafe(24),
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    header = {"typ": "JWT", "alg": TOKEN_ALGORITHM}
    signing_input = ".".join(
        [
            _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
    )
    token = f"{signing_input}.{_sign(signing_input)}"
    return token, payload


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_part, payload_part, signature = token.split(".", 2)
    except ValueError as exc:
        raise AuthError("Malformed token") from exc

    signing_input = f"{header_part}.{payload_part}"
    if not hmac.compare_digest(_sign(signing_input), signature):
        raise AuthError("Invalid token signature")

    try:
        header = json.loads(_b64decode(header_part))
        payload = json.loads(_b64decode(payload_part))
    except (ValueError, json.JSONDecodeError) as exc:
        raise AuthError("Invalid token payload") from exc

    if header.get("alg") != TOKEN_ALGORITHM:
        raise AuthError("Unsupported token algorithm")
    if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
        raise AuthError("Token expired")
    return payload

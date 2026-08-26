from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config.settings import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _create_token(subject: str, token_type: str, expires_delta: timedelta, extra: dict | None = None) -> tuple[str, str]:
    jti = uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "iss": "visionai",
    }
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def create_access_token(user_id: str, role: str) -> tuple[str, str]:
    return _create_token(
        user_id,
        "access",
        timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        {"role": role},
    )


def create_refresh_token(user_id: str) -> tuple[str, str]:
    return _create_token(user_id, "refresh", timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS))


def decode_token(token: str, expected_type: str) -> dict:
    payload = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
        issuer="visionai",
        options={"require": ["exp", "sub", "type", "jti"]},
    )
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("wrong token type")
    return payload


API_KEY_PREFIX = "vk"


def generate_api_key() -> tuple[str, str, str]:
    raw = secrets.token_hex(24)
    key = f"{API_KEY_PREFIX}_live_{raw}"
    key_hash = hash_api_key(key)
    prefix_display = f"{API_KEY_PREFIX}_live_{raw[:4]}…{raw[-4:]}"
    return key, key_hash, prefix_display


def hash_api_key(key: str) -> str:
    return hmac.new(settings.JWT_SECRET.encode(), key.encode(), hashlib.sha256).hexdigest()


def constant_time_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())


def new_request_id() -> str:
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode().rstrip("=")

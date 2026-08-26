from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    hash_password,
    verify_password,
)
from app.db.session import SessionLocal, get_db
from app.models.db_models import (
    ApiKey,
    AuthEvent,
    OneTimeToken,
    RefreshToken,
    User,
    UserRole,
)
from app.schemas import (
    ApiKeyCreate,
    ApiKeyResponse,
    ChangePasswordRequest,
    OneTimeTokenRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.cache_service import cache_set_json
from app.services.email_service import send_reset_email, send_verify_email


def log_auth_event(
    db: Session,
    event: str,
    user_id: str | None = None,
    ip: str | None = None,
    ua: str | None = None,
    detail: dict | None = None,
) -> None:
    db.add(AuthEvent(user_id=user_id, event=event, ip_address=ip, user_agent=ua, detail=detail))


def create_user(db: Session, data: UserCreate, ip: str | None = None, ua: str | None = None) -> User:
    if db.scalar(select(User).where(User.email == data.email)):
        raise ConflictError("Email already registered")
    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole.USER,
    )
    db.add(user)
    db.flush()
    log_auth_event(db, "register", user.id, ip, ua)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email))
    if user and verify_password(password, user.password_hash):
        return user
    return None


def create_tokens(user: User, db: Session | None = None) -> tuple[str, str, str]:
    access, at_jti = create_access_token(user.id, user.role.value)
    refresh, rt_jti = create_refresh_token(user.id)
    if db:
        db.add(RefreshToken(jti=rt_jti, user_id=user.id, expires_at=datetime.now(timezone.utc) + timedelta(days=14)))
    else:
        with SessionLocal() as new_db:
            new_db.add(RefreshToken(jti=rt_jti, user_id=user.id, expires_at=datetime.now(timezone.utc) + timedelta(days=14)))
            new_db.commit()
    return access, refresh, at_jti


def refresh_access_token(refresh_token: str) -> tuple[str, str]:
    try:
        payload = decode_token(refresh_token, "refresh")
    except Exception:
        raise ValidationError("Invalid refresh token")
    with SessionLocal() as db:
        rt = db.get(RefreshToken, payload["jti"])
        if not rt or rt.revoked or rt.expires_at < datetime.now(timezone.utc):
            raise ValidationError("Refresh token revoked or expired")
        user = db.get(User, payload["sub"])
        if not user:
            raise ValidationError("User not found")
        db.execute(delete(RefreshToken).where(RefreshToken.jti == payload["jti"]))
        access, new_rt_jti = create_refresh_token(user.id)
        db.add(
            RefreshToken(
                jti=new_rt_jti,
                user_id=user.id,
                expires_at=datetime.now(timezone.utc) + timedelta(days=14),
            )
        )
        db.commit()
    return access, new_rt_jti


def revoke_refresh_token(jti: str, user_id: str) -> None:
    with SessionLocal() as db:
        db.execute(delete(RefreshToken).where(RefreshToken.jti == jti, RefreshToken.user_id == user_id))
        db.commit()


def revoke_all_refresh_tokens(user_id: str) -> None:
    with SessionLocal() as db:
        db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
        db.commit()


def create_api_key(db: Session, user_id: str, data: ApiKeyCreate) -> tuple[str, ApiKey]:
    raw, key_hash, prefix = generate_api_key()
    api_key = ApiKey(user_id=user_id, name=data.name, key_hash=key_hash, prefix_display=prefix)
    db.add(api_key)
    db.flush()
    return raw, api_key


def revoke_api_key(db: Session, user_id: str, key_id: str) -> bool:
    api_key = db.get(ApiKey, key_id)
    if api_key and api_key.user_id == user_id:
        api_key.revoked = True
        db.commit()
        return True
    return False


def create_reset_token(db: Session, email: str, ip: str | None = None, ua: str | None = None) -> str | None:
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        return None
    token = secrets.token_urlsafe(32)
    token_hash = hash_password(token)
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.add(OneTimeToken(token_hash=token_hash, user_id=user.id, purpose="password_reset", expires_at=expires))
    db.flush()
    if send_reset_email(user.email, token):
        log_auth_event(db, "password_reset_requested", user.id, ip, ua)
        return token
    return None


def consume_reset_token(db: Session, token: str, new_password: str) -> bool:
    token_hash = hash_password(token)
    ot = db.get(OneTimeToken, token_hash)
    if not ot or ot.used or ot.purpose != "password_reset" or ot.expires_at < datetime.now(timezone.utc):
        return False
    user = db.get(User, ot.user_id)
    if not user:
        return False
    user.password_hash = hash_password(new_password)
    ot.used = True
    revoke_all_refresh_tokens(user.id)
    log_auth_event(db, "password_reset_completed", user.id)
    db.commit()
    return True


def create_verify_token(db: Session, user: User) -> str | None:
    token = secrets.token_urlsafe(32)
    token_hash = hash_password(token)
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    db.add(OneTimeToken(token_hash=token_hash, user_id=user.id, purpose="email_verify", expires_at=expires))
    db.flush()
    if send_verify_email(user.email, token):
        return token
    return None


def consume_verify_token(db: Session, token: str) -> bool:
    token_hash = hash_password(token)
    ot = db.get(OneTimeToken, token_hash)
    if not ot or ot.used or ot.purpose != "email_verify" or ot.expires_at < datetime.now(timezone.utc):
        return False
    user = db.get(User, ot.user_id)
    if not user:
        return False
    user.email_verified = True
    ot.used = True
    log_auth_event(db, "email_verified", user.id)
    db.commit()
    return True


def change_password(db: Session, user_id: str, data: ChangePasswordRequest) -> bool:
    user = db.get(User, user_id)
    if not user or not verify_password(data.current_password, user.password_hash):
        return False
    user.password_hash = hash_password(data.new_password)
    revoke_all_refresh_tokens(user_id)
    log_auth_event(db, "password_changed", user_id)
    db.commit()
    return True


def user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        avatar=user.avatar,
        role=user.role.value,
        email_verified=user.email_verified,
        created_at=user.created_at,
    )
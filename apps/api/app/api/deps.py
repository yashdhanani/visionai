from __future__ import annotations

from fastapi import Depends, HTTPException, Request, WebSocket
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.core.security import decode_token, hash_api_key
from app.db.session import get_db
from app.models.db_models import User, ApiKey, UserRole


def verify_api_key(key: str, db: Session) -> User | None:
    from app.models.db_models import utcnow
    key_hash = hash_api_key(key)
    api_key = db.query(ApiKey).filter(ApiKey.key_hash == key_hash, ApiKey.revoked == False).first()  # noqa: E712
    if not api_key:
        return None
    api_key.last_used_at = utcnow()
    try:
        db.commit()
    except Exception:
        db.rollback()
    return db.get(User, api_key.user_id)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    # 1. Check X-API-Key header
    api_key_header = request.headers.get("x-api-key")
    if api_key_header:
        user = verify_api_key(api_key_header, db)
        if not user:
            raise UnauthorizedError("Invalid API key")
        return user

    # 2. Check Authorization header
    auth = request.headers.get("authorization")
    if not auth:
        raise UnauthorizedError("Missing Authorization header")

    scheme, _, token = auth.partition(" ")
    if scheme.lower() == "bearer":
        if token.startswith("vk_live_"):
            user = verify_api_key(token, db)
            if not user:
                raise UnauthorizedError("Invalid API key")
            return user
        try:
            payload = decode_token(token, "access")
        except Exception:
            raise UnauthorizedError("Invalid or expired access token")
        user = db.get(User, payload["sub"])
        if not user:
            raise UnauthorizedError("User not found")
        return user
    else:
        raise UnauthorizedError("Unsupported auth scheme")


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
    api_key_header = request.headers.get("x-api-key")
    if api_key_header:
        return verify_api_key(api_key_header, db)

    auth = request.headers.get("authorization")
    if not auth:
        return None
    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer":
        return None
    if token.startswith("vk_live_"):
        return verify_api_key(token, db)
    try:
        payload = decode_token(token, "access")
    except Exception:
        return None
    return db.get(User, payload["sub"])


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise ForbiddenError("Admin privileges required")
    return user


async def get_current_user_ws(websocket: WebSocket) -> User | None:
    token = websocket.query_params.get("token") or websocket.query_params.get("api_key")
    if not token:
        return None
    try:
        from app.db.session import SessionLocal
        with SessionLocal() as db:
            if token.startswith("vk_live_"):
                return verify_api_key(token, db)
            payload = decode_token(token, "access")
            return db.get(User, payload["sub"])
    except Exception:
        return None


async def require_user_ws(websocket: WebSocket) -> User:
    user = await get_current_user_ws(websocket)
    if not user:
        await websocket.close(code=4001, reason="Authentication required")
        raise RuntimeError("unauthorized")
    return user


def get_current_user_or_apikey(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    return get_current_user(request, db)
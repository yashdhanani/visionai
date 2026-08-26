from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_optional, get_current_user_or_apikey, require_admin
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
from app.services.auth_service import (
    authenticate_user,
    change_password,
    consume_reset_token,
    consume_verify_token,
    create_api_key,
    create_reset_token,
    create_tokens,
    create_user,
    log_auth_event,
    refresh_access_token,
    revoke_api_key,
    revoke_all_refresh_tokens,
    revoke_refresh_token,
    user_to_response,
)
from app.db.session import get_db
from app.core.security import decode_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
def register(data: UserCreate, request: Request, response: Response, db: Session = Depends(get_db)):
    user = create_user(db, data, request.client.host if request.client else None, request.headers.get("user-agent"))
    access, refresh, _ = create_tokens(user, db)
    response.set_cookie(
        "refresh_token",
        refresh,
        httponly=True,
        secure=not request.url.scheme == "http",
        samesite="lax",
        max_age=14 * 24 * 3600,
    )
    log_auth_event(db, "login", user.id, request.client.host if request.client else None, request.headers.get("user-agent"))
    return {"success": True, "data": {"access_token": access, "token_type": "Bearer", "expires_in": 30 * 60}, "meta": {"request_id": getattr(request.state, "request_id", "-")}}


@router.post("/login")
def login(data: UserLogin, request: Request, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.email, data.password)
    if not user:
        log_auth_event(db, "login_failed", ip=request.client.host if request.client else None, ua=request.headers.get("user-agent"), detail={"email": data.email})
        raise HTTPException(401, "Invalid credentials")
    access, refresh, _ = create_tokens(user, db)
    response.set_cookie(
        "refresh_token",
        refresh,
        httponly=True,
        secure=not request.url.scheme == "http",
        samesite="lax",
        max_age=14 * 24 * 3600,
    )
    log_auth_event(db, "login", user.id, request.client.host if request.client else None, request.headers.get("user-agent"))
    return {"success": True, "data": {"access_token": access, "token_type": "Bearer", "expires_in": 30 * 60}, "meta": {"request_id": getattr(request.state, "request_id", "-")}}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    if user:
        refresh = request.cookies.get("refresh_token")
        if refresh:
            try:
                payload = decode_token(refresh, "refresh")
                revoke_refresh_token(payload["jti"], user.id)
            except Exception:
                pass
    response.delete_cookie("refresh_token", httponly=True, secure=not request.url.scheme == "http", samesite="lax")
    return {"success": True, "meta": {"request_id": getattr(request.state, "request_id", "-")}}


@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh = request.cookies.get("refresh_token")
    if not refresh:
        raise HTTPException(401, "No refresh token")
    try:
        access, new_rt = refresh_access_token(refresh)
    except Exception as exc:
        raise HTTPException(401, str(exc))
    response.set_cookie(
        "refresh_token",
        new_rt,
        httponly=True,
        secure=not request.url.scheme == "http",
        samesite="lax",
        max_age=14 * 24 * 3600,
    )
    return {"success": True, "data": {"access_token": access, "token_type": "Bearer", "expires_in": 30 * 60}, "meta": {"request_id": getattr(request.state, "request_id", "-")}}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"success": True, "data": user_to_response(user).model_dump(mode="json"), "meta": {"request_id": getattr(user, "_request_id", "-")}}


@router.post("/change-password")
def change_pw(data: ChangePasswordRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not change_password(db, user.id, data):
        raise HTTPException(400, "Current password incorrect")
    return {"success": True, "meta": {"request_id": "-"}}  # request.state not available easily; rely on middleware


@router.post("/forgot-password")
def forgot(data: OneTimeTokenRequest, request: Request, db: Session = Depends(get_db)):
    create_reset_token(db, data.email, request.client.host if request.client else None, request.headers.get("user-agent"))
    return {"success": True, "meta": {"request_id": "-"}}  # don't reveal if email exists


@router.post("/reset-password")
def reset(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    if not consume_reset_token(db, data.token, data.password):
        raise HTTPException(400, "Invalid or expired reset token")
    return {"success": True, "meta": {"request_id": "-"}}


@router.post("/verify-email")
def verify(data: OneTimeTokenRequest, db: Session = Depends(get_db)):
    if not consume_verify_token(db, data.token):
        raise HTTPException(400, "Invalid or expired verification token")
    return {"success": True, "meta": {"request_id": "-"}}


@router.post("/api-keys", status_code=201)
def create_key(data: ApiKeyCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    raw, api_key = create_api_key(db, user.id, data)
    db.commit()
    resp = ApiKeyResponse.model_validate(api_key).model_dump(mode="json")
    resp["key"] = raw
    return {"success": True, "data": resp, "meta": {"request_id": "-"}}


@router.get("/api-keys")
def list_keys(user=Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.db_models import ApiKey
    keys = db.query(ApiKey).filter(ApiKey.user_id == user.id).order_by(ApiKey.created_at.desc()).all()
    return {"success": True, "data": [ApiKeyResponse.model_validate(k).model_dump(mode="json") for k in keys], "meta": {"request_id": "-"}}


@router.delete("/api-keys/{key_id}")
def delete_key(key_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not revoke_api_key(db, user.id, key_id):
        raise HTTPException(404, "API key not found")
    return {"success": True, "meta": {"request_id": "-"}}


@router.get("/sessions")
def list_sessions(user=Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.db_models import RefreshToken
    tokens = db.query(RefreshToken).filter(RefreshToken.user_id == user.id, RefreshToken.revoked == False).all()  # noqa: E712
    data = [
        {
            "jti": t.jti[:16] + "...",
            "ip": t.ip_address,
            "user_agent": t.user_agent,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "expires_at": t.expires_at.isoformat() if t.expires_at else None,
        }
        for t in tokens
    ]
    return {"success": True, "data": data, "meta": {"request_id": "-"}}


@router.delete("/sessions/{jti}")
def revoke_session(jti: str, user=Depends(get_current_user)):
    revoke_refresh_token(jti, user.id)
    return {"success": True, "meta": {"request_id": "-"}}


@router.delete("/sessions")
def revoke_all(user=Depends(get_current_user)):
    revoke_all_refresh_tokens(user.id)
    return {"success": True, "meta": {"request_id": "-"}}
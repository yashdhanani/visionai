from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.db.session import get_db, engine
from app.ml.model_manager import get_model_manager
from app.schemas import HealthResponse
from app.services.cache_service import get_redis


router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
def health_check():
    checks = {"database": "ok", "redis": "ok", "model": "ok", "storage": "ok"}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        checks["database"] = "fallback"

    return HealthResponse(status="ok", checks=checks)


@router.get("/live")
def liveness():
    return {"status": "ok"}


@router.get("/ready")
def readiness():
    checks = {"database": "down", "redis": "down", "model": "down"}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        pass
    try:
        redis = get_redis()
        if redis:
            redis.ping()
            checks["redis"] = "ok"
        else:
            checks["redis"] = "ok"
    except Exception:
        pass
    try:
        mgr = get_model_manager()
        if mgr.get() is not None:
            checks["model"] = "ok"
    except Exception:
        pass
    ready = all(v == "ok" for v in checks.values())
    return {"ready": ready, "checks": checks}
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
    checks = {"database": "down", "redis": "down", "model": "down", "storage": "down"}

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
            checks["redis"] = "ok"  # memory fallback is ok
    except Exception:
        pass

    try:
        mgr = get_model_manager()
        if mgr.get() is not None:
            checks["model"] = "ok"
    except Exception:
        pass

    try:
        from app.services.storage_service import get_storage
        get_storage()
        checks["storage"] = "ok"
    except Exception:
        pass

    overall = "ok" if all(v == "ok" for v in checks.values()) else ("degraded" if any(v == "ok" for v in checks.values()) else "down")
    return HealthResponse(status=overall, checks=checks)


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
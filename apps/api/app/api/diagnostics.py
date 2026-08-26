from __future__ import annotations

import logging
import time
from typing import Any

import torch
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.ml.model_manager import get_model_manager
from app.config.settings import settings

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])

logger = logging.getLogger("visionai.diagnostics")


@router.get("/health")
async def system_health(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Return detailed system health status."""
    checks = {}

    # Model
    try:
        mgr = get_model_manager()
        model = mgr.get()
        if model is None:
            checks["model"] = {"status": "error", "detail": "No model loaded"}
        else:
            checks["model"] = {"status": "ok", "detail": "Model loaded"}
    except Exception as e:
        checks["model"] = {"status": "error", "detail": str(e)}

    # Device
    device = settings.MODEL_DEVICE
    if device == "auto":
        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
    checks["device"] = {"status": "ok", "detail": device}

    # CUDA availability
    cuda_available = torch.cuda.is_available()
    checks["cuda"] = {"status": "ok" if cuda_available else "warning", "detail": str(cuda_available)}

    # Database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok", "detail": "Connected"}
    except Exception as e:
        checks["database"] = {"status": "error", "detail": str(e)}

    # Redis (optional)
    try:
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        r.ping()
        checks["redis"] = {"status": "ok", "detail": "Connected"}
    except Exception:
        checks["redis"] = {"status": "warning", "detail": "Redis not configured or unreachable"}

    # Overall status
    overall = "ok"
    for k, v in checks.items():
        if v.get("status") == "error":
            overall = "error"
            break
    return {"status": overall, "checks": checks}
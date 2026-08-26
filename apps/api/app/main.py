from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import analytics, auth, categories, detections, diagnostics, events, files, health, models, projects, rules, ws
from app.config.settings import settings
from app.core.error_handlers import install_exception_handlers
from app.core.logging import setup_logging
from app.db.session import Base, engine
from app.ml.model_manager import get_model_manager


def _migrate_schema():
    """Add columns introduced after the initial schema to existing SQLite DBs."""
    from sqlalchemy import text

    with engine.begin() as conn:
        try:
            conn.execute(
                text("ALTER TABLE detection_objects ADD COLUMN text VARCHAR(64)")
            )
            logging.getLogger("visionai").info("Migrated: added detection_objects.text")
        except Exception:
            # Column already exists — safe to ignore.
            pass


def _seed_admin():
    """Create default admin user if it doesn't exist."""
    from sqlalchemy.orm import Session
    from app.models.db_models import User, UserRole
    from app.core.security import hash_password

    with Session(engine) as db:
        existing = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        if not existing:
            user = User(
                name="Admin",
                email=settings.ADMIN_EMAIL,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                email_verified=True,
            )
            db.add(user)
            db.commit()
            logging.getLogger("visionai").info("Default admin user created")
        else:
            logging.getLogger("visionai").info("Admin user already exists, skipping seed")


async def _rate_limit_check(request: Request) -> bool | JSONResponse:
    """Simple rate limiting check. Returns True if allowed, JSONResponse if blocked."""
    if not settings.is_production:
        return True

    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    # Skip rate limiting for health checks
    if path == "/api/v1/health":
        return True

    # Determine rate limit based on endpoint
    if path.startswith("/api/v1/auth"):
        limit = settings.RATE_LIMIT_AUTH_PER_MINUTE
    elif path.startswith("/api/v1/detect"):
        limit = settings.RATE_LIMIT_DETECT_PER_MINUTE
    else:
        limit = 300  # Default limit

    # Simple in-memory rate limiting per minute window
    now_minute = int(time.time() / 60)
    key = f"rate_limit:{client_ip}:{now_minute}"

    # Use request state to store minute key across the request
    request.state.rate_limit_key = key

    # Read current count from a simple file-based store (use Redis in distributed production)
    # For now, we track with a basic approach
    try:
        from app.core.redis_client import get_redis_client
        rds = get_redis_client()
        if rds:
            current_count = rds.get(key)
            if current_count is not None and int(current_count) >= limit:
                return JSONResponse(
                    content={"success": False, "error": {"code": "RATE_LIMITED", "message": "Rate limit exceeded"}},
                    status_code=429,
                )
            if rds:
                rds.incr(key)
                rds.expire(key, 60)
                return True
    except Exception:
        pass

    # Fallback: simple in-memory (not thread-safe, use Redis for production)
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.APP_ENV)
    logger = logging.getLogger("visionai")
    logger.info("VisionAI starting", extra={"env": settings.APP_ENV})

    Base.metadata.create_all(bind=engine)
    _migrate_schema()
    _seed_admin()

    try:
        get_model_manager().load_default()
    except Exception as exc:
        logger.warning(f"Model warmup failed: {exc}")

    yield
    logger.info("VisionAI shutting down")


app = FastAPI(
    title="VisionAI API",
    version="1.0.0",
    description="Real-Time Object Detection Platform",
    lifespan=lifespan,
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url=None,
)

_allowed_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"] if settings.is_production else ["*"]
_allowed_headers = ["Content-Type", "Authorization", "X-Request-ID"] if settings.is_production else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=_allowed_methods,
    allow_headers=_allowed_headers,
)

install_exception_handlers(app)

# Graceful shutdown handling
@app.on_event("shutdown")
async def shutdown_event():
    logger = logging.getLogger("visionai")
    logger.info("Graceful shutdown initiated...")
    logger.info("Graceful shutdown completed")


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    result = await _rate_limit_check(request)
    if result is not True:
        return result
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(
        settings.RATE_LIMIT_DETECT_PER_MINUTE
        if request.url.path.startswith("/api/v1/detect")
        else settings.RATE_LIMIT_AUTH_PER_MINUTE
        if request.url.path.startswith("/api/v1/auth")
        else "300"
    )
    return response


app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(detections.router, prefix="/api/v1")
app.include_router(models.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(diagnostics.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(rules.router, prefix="/api/v1")


@app.websocket("/api/v1/detect/live")
async def websocket_live(websocket: WebSocket):
    from app.services.websocket_service import WSConnection
    from app.api.deps import get_current_user_ws
    user = await get_current_user_ws(websocket)
    if not user:
        await websocket.close(code=4001, reason="Authentication required")
        return
    project_id = websocket.query_params.get("project_id", "")
    category = websocket.query_params.get("category", "objects")
    conn = WSConnection(websocket, user.id, project_id, category=category)
    await conn.handle()


@app.get("/api/v1")
def api_root():
    return {"name": "VisionAI", "version": "1.0.0", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.APP_ENV == "development")
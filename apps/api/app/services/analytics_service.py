from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db_models import Detection, DetectionObject, DetectionSession, Project, SourceType


def _date_trunc_day(db: Session, column):
    """Cross-dialect date truncation to day."""
    from sqlalchemy import text
    if db.bind.dialect.name == "postgresql":
        return func.date_trunc("day", column)
    return func.date(column)


def _date_trunc_hour(db: Session, column):
    if db.bind.dialect.name == "postgresql":
        return func.date_trunc("hour", column)
    return func.strftime("%Y-%m-%d %H:00:00", column)


def _interval_days_ago(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


def get_summary(db: Session, project_id: str | None = None, days: int = 30) -> dict[str, Any]:
    since = _interval_days_ago(days)
    base = (
        select(
            Detection.id,
            Detection.object_count,
            Detection.avg_confidence,
            Detection.fps,
            Detection.processing_time_ms,
        )
        .where(Detection.created_at >= since)
    )
    if project_id:
        base = base.where(Detection.project_id == project_id)

    sub = base.subquery()

    total_dets = db.scalar(select(func.count()).select_from(sub)) or 0
    total_objs = db.scalar(select(func.sum(sub.c.object_count)).select_from(sub)) or 0

    avg_conf = db.scalar(
        select(func.avg(sub.c.avg_confidence)).select_from(sub).where(sub.c.avg_confidence.is_not(None))
    )
    avg_fps = db.scalar(
        select(func.avg(sub.c.fps)).select_from(sub).where(sub.c.fps.is_not(None))
    )
    avg_latency = db.scalar(
        select(func.avg(sub.c.processing_time_ms)).select_from(sub).where(sub.c.processing_time_ms.is_not(None))
    )

    unique_classes = db.scalar(
        select(func.count(func.distinct(DetectionObject.class_name))).join(Detection).where(
            Detection.created_at >= since,
            Detection.project_id == project_id if project_id else True,
        )
    ) or 0

    active_sessions = db.scalar(
        select(func.count(DetectionSession.id)).where(
            DetectionSession.started_at >= since,
            DetectionSession.project_id == project_id if project_id else True,
        )
    ) or 0

    return {
        "total_detections": total_dets,
        "total_objects": total_objs,
        "unique_classes": unique_classes,
        "avg_confidence": round(float(avg_conf or 0), 4),
        "avg_fps": round(float(avg_fps or 0), 1),
        "avg_latency_ms": round(float(avg_latency or 0), 1),
        "active_sessions": active_sessions,
    }


def get_timeseries(db: Session, project_id: str | None = None, days: int = 30, granularity: str = "day") -> list[dict[str, Any]]:
    since = _interval_days_ago(days)
    trunc = _date_trunc_day if granularity == "day" else _date_trunc_hour

    query = (
        select(
            trunc(db, Detection.created_at).label("period"),
            func.count(Detection.id).label("detections"),
            func.sum(Detection.object_count).label("objects"),
        )
        .where(Detection.created_at >= since)
        .group_by("period")
        .order_by("period")
    )
    if project_id:
        query = query.where(Detection.project_id == project_id)

    rows = db.execute(query).all()
    return [
        {"date": r.period.isoformat() if hasattr(r.period, "isoformat") else str(r.period), "detections": r.detections, "objects": r.objects or 0}
        for r in rows
    ]


def get_class_distribution(db: Session, project_id: str | None = None, days: int = 30, limit: int = 20) -> list[dict[str, Any]]:
    since = _interval_days_ago(days)
    query = (
        select(DetectionObject.class_name, func.count(DetectionObject.id).label("count"))
        .join(Detection)
        .where(Detection.created_at >= since)
        .group_by(DetectionObject.class_name)
        .order_by(func.count(DetectionObject.id).desc())
        .limit(limit)
    )
    if project_id:
        query = query.where(Detection.project_id == project_id)
    rows = db.execute(query).all()
    return [{"class_name": r.class_name, "count": r.count} for r in rows]


def get_confidence_histogram(db: Session, project_id: str | None = None, days: int = 30, bins: int = 10) -> list[dict[str, Any]]:
    since = _interval_days_ago(days)
    query = select(DetectionObject.confidence).join(Detection).where(Detection.created_at >= since)
    if project_id:
        query = query.where(Detection.project_id == project_id)
    confs = [r[0] for r in db.execute(query).all()]
    if not confs:
        return []
    step = 1.0 / bins
    hist = [0] * bins
    for c in confs:
        idx = min(int(c / step), bins - 1)
        hist[idx] += 1
    return [{"bin": f"{i*step:.1f}-{(i+1)*step:.1f}", "count": hist[i]} for i in range(bins)]


def get_performance_timeseries(db: Session, project_id: str | None = None, days: int = 30) -> list[dict[str, Any]]:
    since = _interval_days_ago(days)
    query = (
        select(
            _date_trunc_day(db, Detection.created_at).label("date"),
            func.avg(Detection.fps).label("avg_fps"),
            func.avg(Detection.processing_time_ms).label("avg_latency"),
        )
        .where(Detection.created_at >= since, Detection.fps.is_not(None))
        .group_by("date")
        .order_by("date")
    )
    if project_id:
        query = query.where(Detection.project_id == project_id)
    rows = db.execute(query).all()
    return [
        {"date": r.date.isoformat() if hasattr(r.date, "isoformat") else str(r.date), "avg_fps": round(float(r.avg_fps or 0), 1), "avg_latency_ms": round(float(r.avg_latency or 0), 1)}
        for r in rows
    ]


def get_hourly_activity(db: Session, project_id: str | None = None, days: int = 7) -> list[dict[str, Any]]:
    since = _interval_days_ago(days)
    if db.bind.dialect.name == "postgresql":
        hour_col = func.extract("hour", Detection.created_at).label("hour")
    else:
        hour_col = func.strftime("%H", Detection.created_at).label("hour")
    query = (
        select(
            hour_col,
            func.count(Detection.id).label("detections"),
        )
        .where(Detection.created_at >= since)
        .group_by("hour")
        .order_by("hour")
    )
    if project_id:
        query = query.where(Detection.project_id == project_id)
    rows = db.execute(query).all()
    return [{"hour": int(r.hour), "detections": r.detections} for r in rows]
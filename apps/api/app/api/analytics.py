from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.db_models import Project
from app.services.analytics_service import (
    get_class_distribution,
    get_confidence_histogram,
    get_hourly_activity,
    get_performance_timeseries,
    get_summary,
    get_timeseries,
)


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def summary(
    project_id: str | None = Query(None),
    days: int = Query(30, ge=1, le=365),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if project_id:
        proj = db.get(Project, project_id)
        if not proj or proj.user_id != user.id:
            project_id = None
    data = get_summary(db, project_id, days)
    return {"success": True, "data": data, "meta": {"request_id": "-"}}


@router.get("/timeseries")
def timeseries(
    project_id: str | None = Query(None),
    days: int = Query(30, ge=1, le=365),
    granularity: str = Query("day", pattern="^(day|hour)$"),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if project_id:
        proj = db.get(Project, project_id)
        if not proj or proj.user_id != user.id:
            project_id = None
    return {"success": True, "data": get_timeseries(db, project_id, days, granularity), "meta": {"request_id": "-"}}


@router.get("/classes")
def class_distribution(
    project_id: str | None = Query(None),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if project_id:
        proj = db.get(Project, project_id)
        if not proj or proj.user_id != user.id:
            project_id = None
    return {"success": True, "data": get_class_distribution(db, project_id, days, limit), "meta": {"request_id": "-"}}


@router.get("/confidence")
def confidence_histogram(
    project_id: str | None = Query(None),
    days: int = Query(30, ge=1, le=365),
    bins: int = Query(10, ge=5, le=50),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if project_id:
        proj = db.get(Project, project_id)
        if not proj or proj.user_id != user.id:
            project_id = None
    return {"success": True, "data": get_confidence_histogram(db, project_id, days, bins), "meta": {"request_id": "-"}}


@router.get("/performance")
def performance(
    project_id: str | None = Query(None),
    days: int = Query(30, ge=1, le=365),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if project_id:
        proj = db.get(Project, project_id)
        if not proj or proj.user_id != user.id:
            project_id = None
    return {"success": True, "data": get_performance_timeseries(db, project_id, days), "meta": {"request_id": "-"}}


@router.get("/hourly")
def hourly(
    project_id: str | None = Query(None),
    days: int = Query(7, ge=1, le=30),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if project_id:
        proj = db.get(Project, project_id)
        if not proj or proj.user_id != user.id:
            project_id = None
    return {"success": True, "data": get_hourly_activity(db, project_id, days), "meta": {"request_id": "-"}}
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.events.engine import get_event_engine

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/")
async def list_events(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    # Placeholder: return recent events from DB
    return {"success": True, "data": [], "meta": {"count": 0}}


@router.post("/")
async def create_event(
    event_data: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    engine = get_event_engine()
    # In a real implementation, we'd persist to DB
    event = engine.create_event(**event_data)
    engine.emit(event)
    return {"success": True, "data": {"event_id": event.event_id}, "meta": {}}
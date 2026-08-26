from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.rules.engine import get_rule_engine, create_rule_from_config

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("/")
async def list_rules(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    engine = get_rule_engine()
    # Placeholder: return configured rules
    return {"success": True, "data": [], "meta": {"count": 0}}


@router.post("/")
async def create_rule(
    rule_config: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    engine = get_rule_engine()
    # For demo, we just add a simple rule that logs
    rule = create_rule_from_config(rule_config)
    engine.add_rule(rule)
    return {"success": True, "data": {"rule_id": rule.id}, "meta": {}}
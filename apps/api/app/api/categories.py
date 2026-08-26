from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.categories.registry import get_category, list_category_dicts

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("")
def list_categories(user=Depends(get_current_user)):
    return {"success": True, "data": list_category_dicts(), "meta": {"request_id": "-"}}


@router.get("/{category_id}")
def get_category_detail(category_id: str, user=Depends(get_current_user)):
    cat = get_category(category_id)
    if not cat:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": f"Category '{category_id}' not found"}, "meta": {"request_id": "-"}}
    from app.categories.registry import _category_to_dict
    return {"success": True, "data": _category_to_dict(cat), "meta": {"request_id": "-"}}

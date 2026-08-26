from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
import numpy as np
from PIL import Image
import io

from app.api.deps import get_db, get_current_user
from app.ml.face import get_attendance_manager

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/enroll")
async def enroll_user(
    user_id: str,
    name: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    # Read image
    contents = await file.read()
    pil = Image.open(io.BytesIO(contents)).convert("RGB")
    image = np.array(pil)
    manager = get_attendance_manager()
    success = manager.enroll(user_id, name, image)
    return {"success": success, "data": {"user_id": user_id, "name": name}}


@router.post("/verify")
async def verify_user(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    contents = await file.read()
    pil = Image.open(io.BytesIO(contents)).convert("RGB")
    image = np.array(pil)
    manager = get_attendance_manager()
    profile = manager.verify(image)
    if profile:
        return {"success": True, "data": {"user_id": profile.user_id, "name": profile.name}}
    return {"success": False, "data": None, "error": "No match found"}
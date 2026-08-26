from __future__ import annotations

import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_or_apikey
from app.db.session import get_db
from app.models.db_models import Detection
from app.services.storage_service import get_storage


router = APIRouter(prefix="/files", tags=["files"])


@router.get("/{key:path}")
def serve_file(key: str, user=Depends(get_current_user_or_apikey), db: Session = Depends(get_db)):
    """Serve stored file by object key. Ownership checked via detection record."""
    det = db.query(Detection).filter(
        (Detection.original_path == key) | (Detection.annotated_path == key),
        Detection.project.has(user_id=user.id),
    ).first()
    if not det:
        raise HTTPException(404, "File not found or access denied")

    storage = get_storage()
    data = storage.load(key)
    if data is None:
        raise HTTPException(404, "File not found in storage")

    media_type = "image/jpeg" if key.endswith((".jpg", ".jpeg")) else "video/mp4" if key.endswith(".mp4") else "application/octet-stream"
    return StreamingResponse(io.BytesIO(data), media_type=media_type)
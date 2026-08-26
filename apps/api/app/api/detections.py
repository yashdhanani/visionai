from __future__ import annotations

import io
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.db_models import Detection, DetectionObject, DetectionStatus, Project, SourceType
from app.schemas import DetectionListItem, DetectionObjectOut, ImageDetectionResponse, PaginatedResponse, VideoJobStatus
from app.services.detection_service import run_detection_image
from app.services.storage_service import get_storage
from app.services.video_service import start_video_processing


router = APIRouter(prefix="/detections", tags=["detections"])


@router.post("/image")
async def detect_image(
    project_id: str | None = Form(None),
    file: UploadFile = File(...),
    confidence: float | None = Form(None),
    iou: float | None = Form(None),
    model_id: str | None = Form(None),
    classes: str | None = Form(None),
    tracker: str | None = Form(None),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proj = None
    if project_id and project_id != "default":
        proj = db.get(Project, project_id)
        if proj and proj.user_id != user.id:
            proj = None
    if not proj:
        proj = db.query(Project).filter(Project.user_id == user.id).first()
        if not proj:
            proj = Project(user_id=user.id, name="Default Project")
            db.add(proj)
            db.commit()

    class_list = [int(c) for c in classes.split(",")] if classes else None

    file_bytes = await file.read()
    result = await run_detection_image(
        db,
        proj,
        file_bytes,
        file.filename or "image.jpg",
        user.id,
        confidence,
        iou,
        model_id,
        class_list,
        tracker,
    )
    return {"success": True, "data": result.model_dump(mode="json"), "meta": {"request_id": getattr(db, "_request_id", "-")}}


@router.post("/video")
async def detect_video(
    project_id: str | None = Form(None),
    file: UploadFile = File(...),
    confidence: float = Form(0.35),
    iou: float = Form(0.45),
    model_id: str | None = Form(None),
    classes: str | None = Form(None),
    tracker: str | None = Form(None),
    sample_fps: int = Form(10),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proj = None
    if project_id and project_id != "default":
        proj = db.get(Project, project_id)
        if proj and proj.user_id != user.id:
            proj = None
    if not proj:
        proj = db.query(Project).filter(Project.user_id == user.id).first()
        if not proj:
            proj = Project(user_id=user.id, name="Default Project")
            db.add(proj)
            db.commit()

    class_list = [int(c) for c in classes.split(",")] if classes else None

    file_bytes = await file.read()
    det = await start_video_processing(
        db,
        proj,
        file_bytes,
        file.filename or "video.mp4",
        user.id,
        confidence,
        iou,
        model_id,
        class_list,
        tracker,
        sample_fps,
    )
    data = VideoJobStatus(
        detection_id=det.id,
        status=det.status.value,
        progress=det.progress,
        frames_total=det.frames_total,
        frames_done=det.frames_done,
        fps=det.fps,
        objects_detected=det.object_count,
        eta_seconds=None,
        error=det.error_message,
    )
    return {"success": True, "data": data.model_dump(mode="json"), "meta": {"request_id": "-"}}


@router.get("")
def list_detections(
    project_id: str | None = Query(None),
    source_type: SourceType | None = Query(None),
    status: DetectionStatus | None = Query(None),
    class_name: str | None = Query(None),
    min_confidence: float | None = Query(None, ge=0, le=1),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(Detection).join(Project).where(Project.user_id == user.id)
    if project_id:
        query = query.where(Detection.project_id == project_id)
    if source_type:
        query = query.where(Detection.source_type == source_type)
    if status:
        query = query.where(Detection.status == status)
    if class_name:
        query = query.join(DetectionObject).where(DetectionObject.class_name == class_name)
    if min_confidence is not None:
        query = query.where(Detection.avg_confidence >= min_confidence)
    if date_from:
        query = query.where(Detection.created_at >= date_from)
    if date_to:
        query = query.where(Detection.created_at <= date_to)

    query = query.order_by(desc(Detection.created_at))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.execute(query.offset((page - 1) * page_size).limit(page_size)).scalars().all()

    return {"success": True, "data": {"items": [DetectionListItem.model_validate(d).model_dump(mode="json") for d in items], "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}, "meta": {"request_id": "-"}}


@router.get("/{detection_id}")
def get_detection(detection_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    det = db.get(Detection, detection_id)
    if not det or det.project.user_id != user.id:
        raise HTTPException(404, "Detection not found")

    objects = [
        {
            "id": o.id,
            "class_id": o.class_id,
            "class_name": o.class_name,
            "confidence": o.confidence,
            "bbox": {"x": o.x, "y": o.y, "width": o.width, "height": o.height},
            "track_id": o.track_id,
        }
        for o in det.objects
    ]
    data = ImageDetectionResponse(
        id=det.id,
        project_id=det.project_id,
        source_type=det.source_type.value,
        model_id=det.model_id,
        source_url=det.source_url,
        original_path=det.original_path,
        annotated_path=det.annotated_path,
        processing_time_ms=det.processing_time_ms,
        inference_time_ms=det.inference_time_ms,
        fps=det.fps,
        object_count=det.object_count,
        avg_confidence=det.avg_confidence,
        image_width=det.image_width,
        image_height=det.image_height,
        status=det.status.value,
        objects=[DetectionObjectOut(**o) for o in objects],
        created_at=det.created_at,
    )
    return {"success": True, "data": data.model_dump(mode="json"), "meta": {"request_id": "-"}}


@router.get("/{detection_id}/status")
def get_video_status(detection_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    det = db.get(Detection, detection_id)
    if not det or det.project.user_id != user.id:
        raise HTTPException(404, "Detection not found")
    data = VideoJobStatus(
        detection_id=det.id,
        status=det.status.value,
        progress=det.progress,
        frames_total=det.frames_total,
        frames_done=det.frames_done,
        fps=det.fps,
        objects_detected=det.object_count,
        eta_seconds=None,
        error=det.error_message,
    )
    return {"success": True, "data": data.model_dump(mode="json"), "meta": {"request_id": "-"}}


@router.get("/{detection_id}/assets/{kind}")
def get_detection_asset(detection_id: str, kind: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    det = db.get(Detection, detection_id)
    if not det or det.project.user_id != user.id:
        raise HTTPException(404, "Detection not found")

    key = det.annotated_path if kind == "annotated" else det.original_path if kind == "original" else None
    if not key:
        raise HTTPException(404, "Asset not found")

    storage = get_storage()
    data = storage.load(key)
    if data is None:
        raise HTTPException(404, "File not found in storage")

    media_type = "image/jpeg" if kind in ("annotated", "original") else "video/mp4"
    return StreamingResponse(io.BytesIO(data), media_type=media_type)


@router.delete("/{detection_id}")
def delete_detection(detection_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    det = db.get(Detection, detection_id)
    if not det or det.project.user_id != user.id:
        raise HTTPException(404, "Detection not found")

    storage = get_storage()
    for key in (det.original_path, det.annotated_path):
        if key:
            storage.delete(key)
    db.delete(det)
    db.commit()
    return {"success": True, "meta": {"request_id": "-"}}
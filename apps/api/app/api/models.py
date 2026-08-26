from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.ml.model_manager import get_model_manager
from app.models.db_models import MLModel, ModelStatus
from app.schemas import ModelCreate, ModelResponse


router = APIRouter(prefix="/models", tags=["models"])


@router.get("")
def list_models(user=Depends(get_current_user), db: Session = Depends(get_db)):
    models = db.execute(select(MLModel).order_by(desc(MLModel.created_at))).scalars().all()
    return {"success": True, "data": [ModelResponse.model_validate(m).model_dump(mode="json") for m in models], "meta": {"request_id": "-"}}


@router.get("/available")
def list_available_models(user=Depends(get_current_user)):
    mgr = get_model_manager()
    available = mgr.list_available()
    loaded = mgr.list_metadata()
    result = []
    for m in available:
        info = {"id": m["id"], "name": m["name"], "description": m["classes"], "loaded": m["id"] in loaded}
        if m["id"] in loaded:
            info["metadata"] = loaded[m["id"]]
        result.append(info)
    return {"success": True, "data": result, "meta": {"request_id": "-"}}


@router.get("/active")
def get_active_model(user=Depends(get_current_user)):
    mgr = get_model_manager()
    active_id = mgr._active_model_id
    if not active_id:
        return {"success": True, "data": None, "meta": {"request_id": "-"}}
    model = mgr.get(active_id)
    if not model:
        return {"success": True, "data": None, "meta": {"request_id": "-"}}
    meta = model.metadata()
    data = ModelResponse(
        id=active_id,
        name=meta.get("model_path", "unknown"),
        version="1.0",
        framework="ultralytics-yolo",
        path=meta.get("model_path", ""),
        status="active",
        accuracy_map=None,
        classes_count=meta.get("class_count"),
        inference_speed_fps=None,
        created_at=None,
    )
    return {"success": True, "data": data.model_dump(mode="json"), "meta": {"request_id": "-"}}


@router.post("", status_code=201)
def register_model(data: ModelCreate, user=Depends(require_admin), db: Session = Depends(get_db)):
    model = MLModel(name=data.name, version=data.version, path=data.path, framework="ultralytics-yolo")
    db.add(model)
    db.flush()
    return {"success": True, "data": ModelResponse.model_validate(model).model_dump(mode="json"), "meta": {"request_id": "-"}}


@router.post("/{model_id}/activate")
def activate_model(model_id: str, user=Depends(require_admin), db: Session = Depends(get_db)):
    model = db.get(MLModel, model_id)
    if not model:
        raise HTTPException(404, "Model not found")

    mgr = get_model_manager()
    yolo = mgr.get(model_id)
    if yolo is None:
        from app.ml.yolo_model import YOLOModel
        yolo = YOLOModel(model.path)
        yolo.load()
        yolo.warmup((640, 640))
        mgr.register(model_id, yolo)

    mgr.set_active(model_id)

    for m in db.execute(select(MLModel).where(MLModel.status == ModelStatus.ACTIVE)).scalars():
        m.status = ModelStatus.AVAILABLE
    model.status = ModelStatus.ACTIVE
    db.commit()
    return {"success": True, "data": ModelResponse.model_validate(model).model_dump(mode="json"), "meta": {"request_id": "-"}}


@router.post("/{model_id}/deactivate")
def deactivate_model(model_id: str, user=Depends(require_admin), db: Session = Depends(get_db)):
    model = db.get(MLModel, model_id)
    if not model:
        raise HTTPException(404, "Model not found")
    model.status = ModelStatus.AVAILABLE
    mgr = get_model_manager()
    if mgr._active_model_id == model_id:
        mgr._active_model_id = None
    db.commit()
    return {"success": True, "data": ModelResponse.model_validate(model).model_dump(mode="json"), "meta": {"request_id": "-"}}


@router.delete("/{model_id}")
def delete_model(model_id: str, user=Depends(require_admin), db: Session = Depends(get_db)):
    model = db.get(MLModel, model_id)
    if not model:
        raise HTTPException(404, "Model not found")
    mgr = get_model_manager()
    if mgr._active_model_id == model_id:
        mgr._active_model_id = None
    db.delete(model)
    db.commit()
    return {"success": True, "meta": {"request_id": "-"}}
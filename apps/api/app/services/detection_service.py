from __future__ import annotations

import io
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import cv2
import numpy as np
from PIL import Image
from sqlalchemy.orm import Session

from app.core.exceptions import InferenceError, InvalidFileError, ModelUnavailableError
from app.config.settings import settings
from app.schemas import DetectionObjectOut
from app.ml.inference import Detection
from app.ml.model_manager import get_active_model
from app.models.db_models import Detection as DBDetection, DetectionObject, DetectionStatus, MLModel, Project, SourceType
from app.schemas import ImageDetectionResponse
from app.services.storage_service import get_storage, generate_object_key, validate_upload


executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="inference-")
logger = logging.getLogger("visionai.detection")


def _run_inference_sync(
    image: np.ndarray,
    conf: float,
    iou: float,
    classes: list[int] | None,
    tracker: str | None,
    persist: bool,
    model_id: str | None = None,
) -> tuple[list[Detection], dict[str, float], int, int]:
    from app.ml.model_manager import get_model_by_id, get_active_model
    model = get_model_by_id(model_id) if model_id else get_active_model()
    if model is None:
        raise ModelUnavailableError()
    if tracker and tracker != "off":
        res = model.predict_with_tracking(image, conf, iou, tracker, persist, classes)
    else:
        # One-shot images: quality mode
        res = model.predict(image, conf, iou, classes)

    detections = res.detections
    h, w = res.image_height, res.image_width

    from app.ml.enhance import enhance_detections

    detections = enhance_detections(detections, image, w, h, conf, iou)

    perf = {
        "preprocess_ms": res.preprocess_ms,
        "inference_ms": res.inference_ms,
        "postprocess_ms": res.postprocess_ms,
        "total_ms": round(res.preprocess_ms + res.inference_ms + res.postprocess_ms, 2),
    }
    return detections, perf, w, h


def _run_multi_model_sync(
    image: np.ndarray,
    conf: float,
    iou: float,
    classes: list[int] | None,
) -> tuple[list[Detection], dict[str, float], int, int]:
    """Run all available specialized models and merge detections.

    Ensures license plates, faces, and general objects are all detected
    in a single request regardless of which model a user selects.
    """
    from app.ml.model_manager import get_model_by_id

    model_ids = ["default", "plate", "face"]
    all_detections: list[Detection] = []
    total_inference_ms = 0.0
    total_pre_ms = 0.0
    total_post_ms = 0.0
    h, w = image.shape[:2]

    for mid in model_ids:
        try:
            model = get_model_by_id(mid)
            if model is None:
                continue
        except Exception:
            continue
        try:
            if mid == "default":
                # SAHI sliced inference catches small / distant objects
                # (e.g. license plates) that a single full-image pass misses.
                # Finer 512px slices make tiny plates larger relative to the
                # model input, improving recall on small/distant objects.
                res = model.predict_sliced(
                    image, conf, iou, classes, slice_height=512, slice_width=512
                )
            else:
                res = model.predict(image, conf, iou, classes)
        except Exception as exc:
            logger.warning(f"Model {mid} inference failed: {exc}")
            continue
        all_detections.extend(res.detections)
        total_inference_ms += res.inference_ms
        total_pre_ms += res.preprocess_ms
        total_post_ms += res.postprocess_ms

    perf = {
        "preprocess_ms": round(total_pre_ms, 2),
        "inference_ms": round(total_inference_ms, 2),
        "postprocess_ms": round(total_post_ms, 2),
        "total_ms": round(total_pre_ms + total_inference_ms + total_post_ms, 2),
    }

    from app.ml.enhance import enhance_detections

    all_detections = enhance_detections(all_detections, image, w, h, conf, iou)
    return all_detections, perf, w, h


async def run_detection_image(
    db: Session,
    project: Project,
    file_bytes: bytes,
    filename: str,
    user_id: str,
    conf: float | None,
    iou: float | None,
    model_id: str | None,
    classes: list[int] | None,
    tracker: str | None,
) -> ImageDetectionResponse:
    ok, err = validate_upload(filename, file_bytes, settings.max_upload_bytes)
    if not ok:
        raise InvalidFileError(err)

    # load image
    try:
        pil = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        image = np.array(pil)
    except Exception as exc:
        raise InvalidFileError(f"Invalid image: {exc}")

    # model
    if model_id == "auto":
        model = None
    elif model_id:
        from app.ml.model_manager import get_model_by_id
        model = get_model_by_id(model_id)
        if model is None:
            raise InvalidFileError("Model not found")
    else:
        model = get_active_model()
        if model is None:
            raise ModelUnavailableError()

    # inference
    t0 = time.perf_counter()
    loop = None
    try:
        import asyncio
        loop = asyncio.get_running_loop()
    except RuntimeError:
        pass

    conf_val = conf if conf is not None else 0.35
    iou_val = iou if iou is not None else 0.45

    if model_id == "auto":
        if loop:
            detections, perf, w, h = await loop.run_in_executor(
                executor,
                lambda: _run_multi_model_sync(image, conf_val, iou_val, classes),
            )
        else:
            detections, perf, w, h = _run_multi_model_sync(image, conf_val, iou_val, classes)
    elif loop:
        detections, perf, w, h = await loop.run_in_executor(
            executor,
            lambda: _run_inference_sync(image, conf_val, iou_val, classes, tracker, False, model_id=model_id),
        )
    else:
        detections, perf, w, h = _run_inference_sync(image, conf_val, iou_val, classes, tracker, False, model_id=model_id)

    total_ms = round((time.perf_counter() - t0) * 1000, 2)
    fps = round(1000 / total_ms, 2) if total_ms > 0 else 0

    # save original
    storage = get_storage()
    orig_key = generate_object_key(user_id, filename, "originals")
    storage.save(orig_key, file_bytes, "image/jpeg")

    # annotate + save annotated
    anno = image.copy()
    for det in detections:
        x1, y1 = int(det.x), int(det.y)
        x2, y2 = int(det.x + det.width), int(det.y + det.height)
        cv2.rectangle(anno, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"{det.class_name} {det.confidence:.0%}"
        if det.text:
            label = f"{det.class_name} {det.text} {det.confidence:.0%}"
        cv2.putText(anno, label, (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    _, buf = cv2.imencode(".jpg", anno, [cv2.IMWRITE_JPEG_QUALITY, 90])
    anno_key = generate_object_key(user_id, f"anno_{filename}", "annotated")
    storage.save(anno_key, buf.tobytes(), "image/jpeg")

    # Look up real MLModel.id in DB if model_id is a UUID or name
    db_model_uuid = None
    if model_id and model_id != "auto":
        from app.models.db_models import MLModel
        m_rec = db.query(MLModel).filter((MLModel.id == model_id) | (MLModel.name.ilike(f"%{model_id}%"))).first()
        if m_rec:
            db_model_uuid = m_rec.id

    # persist
    db_det = DBDetection(
        project_id=project.id,
        model_id=db_model_uuid,
        source_type=SourceType.IMAGE,
        source_url=None,
        original_path=orig_key,
        annotated_path=anno_key,
        processing_time_ms=perf["total_ms"],
        inference_time_ms=perf["inference_ms"],
        fps=fps,
        object_count=len(detections),
        avg_confidence=round(sum(d.confidence for d in detections) / len(detections), 4) if detections else None,
        image_width=w,
        image_height=h,
        status=DetectionStatus.COMPLETED,
    )
    db.add(db_det)
    db.flush()

    for det in detections:
        db.add(
            DetectionObject(
                detection_id=db_det.id,
                class_id=det.class_id,
                class_name=det.class_name,
                confidence=det.confidence,
                x=det.x,
                y=det.y,
                width=det.width,
                height=det.height,
                track_id=det.track_id,
                text=det.text,
            )
        )
    db.commit()

    # response
    objects = [
        {
            "class_id": d.class_id,
            "class_name": d.class_name,
            "confidence": d.confidence,
            "bbox": {"x": d.x, "y": d.y, "width": d.width, "height": d.height},
            "track_id": d.track_id,
            "text": d.text,
        }
        for d in detections
    ]
    return ImageDetectionResponse(
        id=db_det.id,
        project_id=project.id,
        source_type="image",
        model_id=model_id,
        source_url=None,
        original_path=orig_key,
        annotated_path=anno_key,
        processing_time_ms=perf["total_ms"],
        inference_time_ms=perf["inference_ms"],
        fps=fps,
        object_count=len(detections),
        avg_confidence=db_det.avg_confidence,
        image_width=w,
        image_height=h,
        status="completed",
        objects=[DetectionObjectOut(**o) for o in objects],
        created_at=db_det.created_at,
    )


from app.config.settings import settings
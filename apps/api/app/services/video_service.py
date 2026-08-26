from __future__ import annotations

import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.db.session import SessionLocal
from app.ml.inference import Detection
from app.ml.model_manager import get_active_model
from app.models.db_models import (
    Detection as DBDetection,
    DetectionObject,
    DetectionStatus,
    Project,
    SourceType,
)
from app.services.storage_service import get_storage, generate_object_key, validate_upload

video_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="video-worker-")
logger = logging.getLogger("visionai.video")


def _probe_codec() -> str:
    test_path = "/tmp/visionai_codec_test.mp4"
    for fourcc_str in ("avc1", "vp09", "vp80", "mp4v"):
        fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
        writer = cv2.VideoWriter(test_path, fourcc, 30.0, (640, 360))
        if writer.isOpened():
            writer.write(np.zeros((360, 640, 3), dtype=np.uint8))
            writer.release()
            try:
                Path(test_path).unlink()
            except Exception:
                pass
            return fourcc_str
    return "mp4v"


_DEFAULT_CODEC = _probe_codec()


def _process_video_sync(
    input_path: str,
    output_path: str,
    conf: float,
    iou: float,
    classes: list[int] | None,
    tracker: str | None,
    sample_fps: int,
) -> dict[str, Any]:
    model = get_active_model()
    if model is None:
        raise RuntimeError("Model unavailable")

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError("Cannot open video")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    stride = max(1, round(src_fps / sample_fps))
    out_fps = src_fps / stride

    fourcc = cv2.VideoWriter_fourcc(*_DEFAULT_CODEC)
    writer = cv2.VideoWriter(output_path, fourcc, out_fps, (width, height))

    frame_idx = 0
    written = 0
    total_objects = 0
    infer_start = time.perf_counter()

    persist = tracker is not None and tracker != "off"

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % stride != 0:
            frame_idx += 1
            continue

        if tracker and tracker != "off":
            res = model.predict_with_tracking(frame, conf, iou, tracker, persist, classes)
        else:
            res = model.predict(frame, conf, iou, classes)

        from app.ml.enhance import enhance_detections

        detections = enhance_detections(res.detections, frame, width, height, conf, iou)

        total_objects += len(detections)

        for det in detections:
            x1, y1 = int(det.x), int(det.y)
            x2, y2 = int(det.x + det.width), int(det.y + det.height)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{det.class_name} {det.confidence:.0%}"
            if det.text:
                label = f"{det.class_name} {det.text} {det.confidence:.0%}"
            if det.track_id is not None:
                label += f" #{det.track_id}"
            cv2.putText(frame, label, (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        writer.write(frame)
        written += 1
        frame_idx += 1

    infer_end = time.perf_counter()
    cap.release()
    writer.release()

    return {
        "frames_total": total_frames,
        "frames_processed": written,
        "fps": round(written / max(infer_end - infer_start, 0.001), 2),
        "objects": total_objects,
        "duration_ms": round((infer_end - infer_start) * 1000, 2),
    }


def _mark_failed(db: Session, detection_id: str, error: str) -> None:
    det = db.get(DBDetection, detection_id)
    if det:
        det.status = DetectionStatus.FAILED
        det.error_message = error
        det.progress = 100.0
        db.commit()


async def process_video_job(
    detection_id: str,
    input_key: str,
    filename: str,
    project_id: str,
    conf: float,
    iou: float,
    model_id: str | None,
    classes: list[int] | None,
    tracker: str | None,
    sample_fps: int,
) -> None:
    db = SessionLocal()
    try:
        storage = get_storage()
        input_data = storage.load(input_key)
        if input_data is None:
            _mark_failed(db, detection_id, "Source file not found in storage")
            return

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp_in:
            tmp_in.write(input_data)
            in_path = tmp_in.name

        out_path = in_path.replace(".", "_out.")

        try:
            import asyncio
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                video_executor,
                lambda: _process_video_sync(in_path, out_path, conf, iou, classes, tracker, sample_fps),
            )

            with open(out_path, "rb") as f:
                out_bytes = f.read()

            out_key = generate_object_key(project_id, f"processed_{filename}", "videos")
            storage.save(out_key, out_bytes, "video/mp4")

            det = db.get(DBDetection, detection_id)
            if det:
                det.annotated_path = out_key
                det.status = DetectionStatus.COMPLETED
                det.progress = 100.0
                det.frames_total = result["frames_total"]
                det.frames_done = result["frames_processed"]
                det.fps = result["fps"]
                det.object_count = result["objects"]
                det.processing_time_ms = result["duration_ms"]
                db.commit()

        except Exception as exc:
            logger.exception(f"Video processing failed for {detection_id}")
            _mark_failed(db, detection_id, str(exc))
        finally:
            try:
                Path(in_path).unlink(missing_ok=True)
                Path(out_path).unlink(missing_ok=True)
            except Exception:
                pass
    finally:
        db.close()


async def start_video_processing(
    db: Session,
    project: Project,
    file_bytes: bytes,
    filename: str,
    user_id: str,
    conf: float,
    iou: float,
    model_id: str | None,
    classes: list[int] | None,
    tracker: str | None,
    sample_fps: int,
) -> DBDetection:
    ok, err = validate_upload(filename, file_bytes, settings.max_video_upload_bytes)
    if not ok:
        from app.core.exceptions import InvalidFileError
        raise InvalidFileError(err)

    storage = get_storage()
    input_key = generate_object_key(user_id, filename, "videos")
    storage.save(input_key, file_bytes, "video/mp4")

    det = DBDetection(
        project_id=project.id,
        model_id=model_id,
        source_type=SourceType.VIDEO,
        source_url=None,
        original_path=input_key,
        annotated_path=None,
        status=DetectionStatus.PROCESSING,
        progress=0.0,
        processing_time_ms=0.0,
    )
    db.add(det)
    db.flush()
    db.commit()

    import asyncio
    asyncio.create_task(
        process_video_job(
            det.id,
            input_key,
            filename,
            project.id,
            conf,
            iou,
            model_id,
            classes,
            tracker,
            sample_fps,
        )
    )
    return det
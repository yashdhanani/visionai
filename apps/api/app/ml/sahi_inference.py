from __future__ import annotations

import logging
from typing import Any

import numpy as np

from app.ml.inference import Detection, InferenceResult

logger = logging.getLogger("visionai.ml.sahi")

# Classes that benefit from sliced (high-resolution tile) inference.
# Distant / small license plates are the primary target.
PLATE_CLASS_NAMES = {"L", "license_plate", "plate"}


def sliced_predict(
    model_path: str,
    image: np.ndarray,
    conf: float,
    iou: float,
    classes: list[int] | None = None,
    slice_height: int = 640,
    slice_width: int = 640,
    overlap_height_ratio: float = 0.2,
    overlap_width_ratio: float = 0.2,
    device: str = "cpu",
    class_names: dict[int, str] | None = None,
) -> InferenceResult:
    """Slicing Aided Hyper Inference (SAHI) for small / distant object detection.

    Partitions the image into overlapping tiles, runs detection on each tile,
    then merges results. This is the state-of-the-art technique for detecting
    small objects (e.g. license plates at a distance) that a single full-image
    pass would miss.
    """
    try:
        from sahi import AutoDetectionModel
        from sahi.predict import get_sliced_prediction
    except ImportError as exc:
        raise RuntimeError("sahi is not installed") from exc

    detection_model = AutoDetectionModel.from_pretrained(
        model_type="ultralytics",
        model_path=model_path,
        confidence_threshold=conf,
        device=device,
        image_size=640,
    )

    result = get_sliced_prediction(
        image,
        detection_model,
        slice_height=slice_height,
        slice_width=slice_width,
        overlap_height_ratio=overlap_height_ratio,
        overlap_width_ratio=overlap_width_ratio,
        postprocess_match_threshold=iou,
        verbose=0,
    )

    h, w = image.shape[:2]
    detections: list[Detection] = []
    for obj in result.object_prediction_list:
        score = float(obj.score.value)
        if score < conf:
            continue
        cid = int(obj.category.id)
        if classes is not None and cid not in classes:
            continue
        x1, y1, x2, y2 = obj.bbox.to_xyxy()
        name = class_names.get(cid, obj.category.name) if class_names else obj.category.name
        detections.append(
            Detection(
                class_id=cid,
                class_name=name,
                confidence=score,
                x=float(x1),
                y=float(y1),
                width=float(x2 - x1),
                height=float(y2 - y1),
            )
        )

    return InferenceResult(
        detections=detections,
        image_width=w,
        image_height=h,
        preprocess_ms=0.0,
        inference_ms=0.0,
        postprocess_ms=0.0,
    )

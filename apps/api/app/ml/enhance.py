from __future__ import annotations

import numpy as np

from app.ml.inference import Detection
from app.ml.ocr import read_plate
from app.ml.sahi_inference import PLATE_CLASS_NAMES
from app.ml.postprocess import refine


def enhance_detections(
    detections: list[Detection],
    image: np.ndarray,
    image_w: int,
    image_h: int,
    conf: float = 0.35,
    iou: float = 0.45,
    do_ocr: bool = True,
    pad_ratio: float = 0.02,
) -> list[Detection]:
    """Shared post-processing for every inference path (image / video / live).

    Applies OCR to license plates (tightening the box to the character region)
    and runs the refine pipeline (clip -> noise filter -> containment
    suppression -> NMS -> padding) so all paths produce consistent, clean,
    accurate area coverage.
    """
    if do_ocr:
        for det in detections:
            if det.class_name in PLATE_CLASS_NAMES:
                x1, y1 = max(0, int(det.x)), max(0, int(det.y))
                x2, y2 = min(image_w, int(det.x + det.width)), min(image_h, int(det.y + det.height))
                crop = image[y1:y2, x1:x2]
                text, ocr_conf, bbox = read_plate(crop)
                if text:
                    det.text = text
                    det.confidence = round(0.7 * det.confidence + 0.3 * ocr_conf, 4)
                    if bbox:
                        bx1, by1, bx2, by2 = bbox
                        det.x = float(x1 + bx1)
                        det.y = float(y1 + by1)
                        det.width = float(bx2 - bx1)
                        det.height = float(by2 - by1)

    return refine(
        detections,
        image_w,
        image_h,
        iou_threshold=iou,
        exempt_classes=PLATE_CLASS_NAMES | {"face"},
        pad_ratio=pad_ratio,
    )

from __future__ import annotations

import logging

from app.ml.inference import Detection

logger = logging.getLogger("visionai.ml.postprocess")


def _iou(a: Detection, b: Detection) -> float:
    ax1, ay1, ax2, ay2 = a.x, a.y, a.x + a.width, a.y + a.height
    bx1, by1, bx2, by2 = b.x, b.y, b.x + b.width, b.y + b.height
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def nms_detections(
    detections: list[Detection],
    iou_threshold: float = 0.5,
    same_class_only: bool = True,
) -> list[Detection]:
    """Non-Maximum Suppression across a merged detection list.

    Removes overlapping duplicate boxes (same object detected by multiple
    models or SAHI tiles) keeping the highest-confidence prediction. This is
    what makes the covered area clean instead of multiple stacked boxes.
    """
    dets = sorted(detections, key=lambda d: d.confidence, reverse=True)
    kept: list[Detection] = []
    while dets:
        best = dets.pop(0)
        kept.append(best)
        survivors = []
        for d in dets:
            if same_class_only and d.class_name != best.class_name:
                survivors.append(d)
                continue
            if _iou(best, d) > iou_threshold:
                continue  # suppress duplicate covering the same area
            survivors.append(d)
        dets = survivors
    return kept


def suppress_contained(
    detections: list[Detection],
    containment_threshold: float = 0.9,
    area_ratio_min: float = 0.33,
    area_ratio_max: float = 3.0,
    exempt_classes: set[str] | None = None,
) -> list[Detection]:
    """Suppress a false-positive box almost fully contained in a stronger,
    comparable-sized box of a different class (e.g. a stray 'person' box
    overlapping a 'car'). Uses containment (how much of the weaker box sits
    inside the stronger one) rather than IoU so a smaller box fully inside a
    larger one is correctly removed. Never touches exempt classes (plate/face)
    so a small plate inside a car is always preserved.
    """
    exempt = exempt_classes or set()
    dets = sorted(detections, key=lambda d: d.confidence, reverse=True)
    kept: list[Detection] = []
    while dets:
        best = dets.pop(0)
        kept.append(best)
        survivors = []
        for d in dets:
            if d.class_name in exempt or best.class_name in exempt:
                survivors.append(d)
                continue
            if d.class_name == best.class_name:
                survivors.append(d)
                continue
            inter = _intersection_area(best, d)
            area_d = d.width * d.height
            if area_d <= 0 or inter / area_d < containment_threshold:
                survivors.append(d)
                continue
            area_best = best.width * best.height
            ratio = (area_d / area_best) if area_best > 0 else 0.0
            if area_ratio_min <= ratio <= area_ratio_max:
                continue  # false positive: suppress
            survivors.append(d)
        dets = survivors
    return kept


def _intersection_area(a: Detection, b: Detection) -> float:
    ax1, ay1, ax2, ay2 = a.x, a.y, a.x + a.width, a.y + a.height
    bx1, by1, bx2, by2 = b.x, b.y, b.x + b.width, b.y + b.height
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    return iw * ih


def filter_detections(
    detections: list[Detection],
    image_w: int,
    image_h: int,
    min_area_ratio: float = 0.0005,
    min_confidence: float = 0.05,
    exempt_classes: set[str] | None = None,
) -> list[Detection]:
    """Drop spurious false-positive boxes that cover tiny/wrong areas.

    Classes in ``exempt_classes`` (e.g. license plates, faces) are kept
    regardless of size because they are intentionally small.
    """
    img_area = float(image_w * image_h)
    exempt = exempt_classes or set()
    out = []
    for d in detections:
        if d.confidence < min_confidence:
            continue
        # Clamp boxes to the image so the covered area never spills outside.
        x1 = max(0.0, min(d.x, float(image_w)))
        y1 = max(0.0, min(d.y, float(image_h)))
        x2 = max(x1, min(d.x + d.width, float(image_w)))
        y2 = max(y1, min(d.y + d.height, float(image_h)))
        d.x, d.y = x1, y1
        d.width, d.height = x2 - x1, y2 - y1
        if d.class_name in exempt:
            out.append(d)
            continue
        area = d.width * d.height
        if img_area > 0 and area / img_area < min_area_ratio:
            continue
        out.append(d)
    return out


def refine(
    detections: list[Detection],
    image_w: int,
    image_h: int,
    iou_threshold: float = 0.5,
    exempt_classes: set[str] | None = None,
    pad_ratio: float = 0.0,
) -> list[Detection]:
    """Full post-processing pipeline for clean, accurate area coverage.

    Order: clip to frame -> drop tiny noise -> suppress contained false
    positives -> NMS duplicate boxes -> optional outward padding (so objects
    are never cut off).
    """
    detections = filter_detections(
        detections, image_w, image_h, exempt_classes=exempt_classes
    )
    detections = suppress_contained(
        detections, exempt_classes=exempt_classes
    )
    detections = nms_detections(detections, iou_threshold=iou_threshold)

    if pad_ratio > 0:
        exempt = exempt_classes or set()
        for d in detections:
            if d.class_name in exempt:
                continue  # keep plates/faces tight (OCR-defined)
            pad_x = d.width * pad_ratio
            pad_y = d.height * pad_ratio
            d.x = max(0.0, d.x - pad_x)
            d.y = max(0.0, d.y - pad_y)
            d.width = min(float(image_w), d.x + d.width + pad_x * 2) - d.x
            d.height = min(float(image_h), d.y + d.height + pad_y * 2) - d.y
    return detections

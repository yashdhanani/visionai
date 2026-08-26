from __future__ import annotations

import logging

import cv2
import numpy as np

logger = logging.getLogger("visionai.ml.ocr")

_reader = None


def get_reader(langs: list[str] | None = None, gpu: bool = False):
    """Lazily instantiate the EasyOCR reader (heavy model load)."""
    global _reader
    if _reader is None:
        try:
            import easyocr
        except ImportError:
            logger.warning("easyocr not installed; license-plate OCR disabled")
            return None
        _reader = easyocr.Reader(langs or ["en"], gpu=gpu)
    return _reader


def read_plate(crop: np.ndarray, langs: list[str] | None = None) -> tuple[str, float, tuple[int, int, int, int] | None]:
    """Run OCR on a cropped plate region.

    Returns (text, avg_confidence, tight_bbox) where ``tight_bbox`` is the
    tight bounding box of the recognized characters in crop coordinates
    (x1, y1, x2, y2) or None when no text was found.
    """
    if crop is None or crop.size == 0:
        return "", 0.0, None

    reader = get_reader(langs)
    if reader is None:
        return "", 0.0, None

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.ndim == 3 else crop

    # Improve contrast for faded / low-light plates.
    gray = cv2.equalizeHist(gray)

    h, w = gray.shape[:2]
    if h == 0 or w == 0:
        return "", 0.0, None

    # Deskew: correct slight rotations so characters read cleanly.
    gray = _deskew(gray)

    # Upscale small crops so OCR reads characters reliably.
    scale = max(1, int(200 / h))
    resized = cv2.resize(gray, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)

    try:
        results = reader.readtext(
            resized,
            detail=1,
            paragraph=False,
            allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        )
    except Exception:
        results = reader.readtext(resized, detail=1, paragraph=False)

    texts: list[str] = []
    confs: list[float] = []
    xs: list[int] = []
    ys: list[int] = []
    for box, text, conf in results:
        texts.append(text)
        confs.append(float(conf))
        pts = box if isinstance(box, list) else box.tolist()
        for px, py in pts:
            xs.append(int(px))
            ys.append(int(py))

    scaled = max(1, scale)
    bbox = (min(xs) // scaled, min(ys) // scaled, max(xs) // scaled, max(ys) // scaled) if xs else None

    full = "".join(texts).upper().replace(" ", "")
    avg = sum(confs) / len(confs) if confs else 0.0
    return full, avg, bbox


def _deskew(gray: np.ndarray) -> np.ndarray:
    """Correct slight rotation of a plate using its dominant text angle."""
    try:
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=max(20, gray.shape[0] // 4))
        if lines is None:
            return gray
        angles = []
        for rho, theta in lines[:20]:
            deg = (theta * 180.0 / np.pi) - 90.0
            if -45 < deg < 45:
                angles.append(deg)
        if not angles:
            return gray
        median = float(np.median(angles))
        if abs(median) < 0.5:
            return gray
        (h, w) = gray.shape[:2]
        center = (w // 2, h // 2)
        rot = cv2.getRotationMatrix2D(center, median, 1.0)
        return cv2.warpAffine(gray, rot, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    except Exception:
        return gray

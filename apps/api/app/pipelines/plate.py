from __future__ import annotations

import io
import logging
from typing import Any

import cv2
import numpy as np
from PIL import Image

import re

from app.ml.inference import Detection
from app.ml.model_manager import get_model_by_id

logger = logging.getLogger("visionai.plate")

# Plate text: alphanumeric only (production OCR constraint)
_PLATE_CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


class PlatePipeline:
    def __init__(self, plate_model_id: str = "plate", ocr_lang: str = "eng"):
        self.plate_model_id = plate_model_id
        self.ocr_lang = ocr_lang
        self._model = None
        self._tesseract_available = False

    def _load_model(self):
        if self._model is None:
            self._model = get_model_by_id(self.plate_model_id)
        return self._model

    def _crop_plate(self, frame: np.ndarray, det: Detection) -> np.ndarray:
        x = int(det.x)
        y = int(det.y)
        w = int(det.width)
        h = int(det.height)
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(frame.shape[1], x + w)
        y2 = min(frame.shape[0], y + h)
        return frame[y1:y2, x1:x2]

    def _enhance_plate(self, crop: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
        # Upscale small crops (spec: image enhancement) for better OCR
        h, w = gray.shape
        if h < 64 or w < 200:
            scale = max(2, int(np.ceil(128 / max(h, 1))))
            gray = cv2.resize(gray, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def _ocr_image(self, image: np.ndarray) -> tuple[str, float]:
        try:
            import pytesseract
            self._tesseract_available = True
        except ImportError:
            return "", 0.0

        try:
            pil = Image.fromarray(image)
            text = pytesseract.image_to_string(
                pil,
                config=f"--psm 8 -l {self.ocr_lang} -c tessedit_char_whitelist={_PLATE_CHARSET}",
            ).strip()
            conf = 0.8 if text else 0.0  # Simplified confidence
            return text, conf
        except Exception as e:
            logger.warning(f"OCR failed: {e}")
            return "", 0.0

    @staticmethod
    def normalize_plate(text: str) -> str:
        """Uppercase + strip non-plate characters (spec: character normalization)."""
        return re.sub(r"[^A-Z0-9]", "", text.upper())

    def process(self, frame: np.ndarray, detections: list[Detection]) -> list[dict[str, Any]]:
        results = []
        for det in detections:
            # Assume detections from plate model (class_id 0 = plate)
            if det.class_id != 0:
                continue
            crop = self._crop_plate(frame, det)
            if crop.size == 0:
                continue
            enhanced = self._enhance_plate(crop)
            text, conf = self._ocr_image(enhanced)
            if text:
                results.append({
                    "plate_text": text,
                    "ocr_confidence": conf,
                    "bbox": {"x": det.x, "y": det.y, "width": det.width, "height": det.height},
                    "track_id": det.track_id,
                })
        return results
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np
import cv2


@dataclass
class Detection:
    class_id: int
    class_name: str
    confidence: float
    x: float
    y: float
    width: float
    height: float
    track_id: int | None = None
    text: str | None = None


@dataclass
class InferenceResult:
    detections: list[Detection]
    image_width: int
    image_height: int
    preprocess_ms: float
    inference_ms: float
    postprocess_ms: float


class DetectionModel(ABC):
    @property
    @abstractmethod
    def class_names(self) -> dict[int, str]: ...

    @abstractmethod
    def warmup(self, shape: tuple[int, int]) -> None: ...

    @abstractmethod
    def predict(self, image: np.ndarray, conf: float, iou: float, classes: list[int] | None = None) -> InferenceResult: ...

    @abstractmethod
    def predict_with_tracking(
        self,
        image: np.ndarray,
        conf: float,
        iou: float,
        tracker: str,
        persist: bool,
        classes: list[int] | None = None,
    ) -> InferenceResult: ...

    @abstractmethod
    def metadata(self) -> dict[str, Any]: ...


def letterbox(image: np.ndarray, new_shape: tuple[int, int], color=(114, 114, 114)) -> tuple[np.ndarray, float, tuple[float, float]]:
    """Resize with unchanged aspect ratio using padding."""
    h, w = image.shape[:2]
    nh, nw = new_shape
    scale = min(nw / w, nh / h)
    nw_scaled, nh_scaled = int(round(w * scale)), int(round(h * scale))
    resized = np.array(np.zeros((nh, nw, 3), dtype=np.uint8)) + color
    resized[:nh_scaled, :nw_scaled] = cv2.resize(image, (nw_scaled, nh_scaled), interpolation=cv2.INTER_LINEAR)
    pad_w = (nw - nw_scaled) / 2
    pad_h = (nh - nh_scaled) / 2
    return resized, scale, (pad_w, pad_h)


def unletterbox_boxes(
    boxes: np.ndarray,
    scale: float,
    pad: tuple[float, float],
    orig_shape: tuple[int, int],
) -> np.ndarray:
    """Map letterboxed boxes back to original image coordinates."""
    pad_w, pad_h = pad
    boxes = boxes.copy()
    boxes[:, [0, 2]] = (boxes[:, [0, 2]] - pad_w) / scale
    boxes[:, [1, 3]] = (boxes[:, [1, 3]] - pad_h) / scale
    h, w = orig_shape[:2]
    boxes[:, [0, 2]] = np.clip(boxes[:, [0, 2]], 0, w)
    boxes[:, [1, 3]] = np.clip(boxes[:, [1, 3]], 0, h)
    return boxes
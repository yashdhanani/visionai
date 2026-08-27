from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np
import torch

from app.ml.inference import Detection, DetectionModel, InferenceResult

logger = logging.getLogger("visionai.ml")


def _to_bgr(image: np.ndarray) -> np.ndarray:
    """Ultralytics expects numpy arrays in BGR (cv2 convention); our pipeline is RGB."""
    import cv2

    return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)


class YOLOModel(DetectionModel):
    def __init__(self, model_path: str, device: str = "auto") -> None:
        self.model_path = model_path
        self.device = self._resolve_device(device)
        self._model = None
        self._class_names: dict[int, str] = {}
        self._tracker_available = False

    @staticmethod
    def _resolve_device(device: str) -> str:
        if device != "auto":
            return device
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def load(self) -> None:
        if self._model is not None:
            return
        try:
            from ultralytics import YOLO
        except ImportError:
            raise RuntimeError("ultralytics not installed")
        self._model = YOLO(self.model_path)
        self._model.to(self.device)
        self._class_names = getattr(self._model.model, "names", {})
        if hasattr(self._model, "predictor") and self._model.predictor is not None:
            self._tracker_available = True
        logger.info(
            f"YOLO model loaded: {self.model_path} on {self.device}",
            extra={"model": self.model_path, "device": self.device},
        )

    def warmup(self, shape: tuple[int, int]) -> None:
        if self._model is None:
            self.load()
        h, w = shape
        dummy = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
        self._model(dummy, verbose=False, device=self.device)

    def predict(
        self,
        image: np.ndarray,
        conf: float,
        iou: float,
        classes: list[int] | None = None,
        imgsz: int = 640,
        augment: bool = False,
    ) -> InferenceResult:
        if self._model is None:
            self.load()

        orig_h, orig_w = image.shape[:2]
        t0 = time.perf_counter()
        t_pre = t0

        with torch.inference_mode():
            results = self._model(
                _to_bgr(image),
                conf=conf,
                iou=iou,
                classes=classes,
                augment=augment,
                imgsz=imgsz,
                verbose=False,
            )
        t_inf = time.perf_counter()

        detections = []
        for r in results:
            if r.boxes is None:
                continue
            boxes = r.boxes.xyxy.cpu().numpy()
            confs = r.boxes.conf.cpu().numpy()
            cls_ids = r.boxes.cls.cpu().numpy().astype(int)
            for box, cf, cid in zip(boxes, confs, cls_ids):
                x1, y1, x2, y2 = box
                detections.append(
                    Detection(
                        class_id=int(cid),
                        class_name=self._class_names.get(int(cid), str(int(cid))),
                        confidence=float(cf),
                        x=float(x1),
                        y=float(y1),
                        width=float(x2 - x1),
                        height=float(y2 - y1),
                    )
                )
        t_post = time.perf_counter()

        return InferenceResult(
            detections=detections,
            image_width=orig_w,
            image_height=orig_h,
            preprocess_ms=round((t_pre - t0) * 1000, 2),
            inference_ms=round((t_inf - t_pre) * 1000, 2),
            postprocess_ms=round((t_post - t_inf) * 1000, 2),
        )

    def predict_sliced(
        self,
        image: np.ndarray,
        conf: float,
        iou: float,
        classes: list[int] | None = None,
        slice_height: int = 640,
        slice_width: int = 640,
    ) -> InferenceResult:
        """SAHI sliced inference for small / distant object detection."""
        from app.ml.sahi_inference import sliced_predict

        return sliced_predict(
            self.model_path,
            image,
            conf,
            iou,
            classes,
            slice_height=slice_height,
            slice_width=slice_width,
            device=self.device,
            class_names=self._class_names,
        )

    def predict_with_tracking(
        self,
        image: np.ndarray,
        conf: float,
        iou: float,
        tracker: str,
        persist: bool,
        classes: list[int] | None = None,
        imgsz: int = 640,
    ) -> InferenceResult:
        if self._model is None:
            self.load()

        orig_h, orig_w = image.shape[:2]
        t0 = time.perf_counter()
        t_pre = t0

        tracker_cfg = "bytetrack.yaml" if tracker == "bytetrack" else ("botsort.yaml" if tracker == "botsort" else None)

        with torch.inference_mode():
            results = self._model.track(
                _to_bgr(image),
                conf=conf,
                iou=iou,
                classes=classes,
                persist=persist,
                tracker=tracker_cfg,
                augment=False,
                imgsz=imgsz,
                verbose=False,
            )
        t_inf = time.perf_counter()

        detections = []
        for r in results:
            if r.boxes is None:
                continue
            boxes = r.boxes.xyxy.cpu().numpy()
            confs = r.boxes.conf.cpu().numpy()
            cls_ids = r.boxes.cls.cpu().numpy().astype(int)
            track_ids = r.boxes.id.cpu().numpy().astype(int) if r.boxes.id is not None else [None] * len(cls_ids)
            for box, cf, cid, tid in zip(boxes, confs, cls_ids, track_ids):
                x1, y1, x2, y2 = box
                detections.append(
                    Detection(
                        class_id=int(cid),
                        class_name=self._class_names.get(int(cid), str(int(cid))),
                        confidence=float(cf),
                        x=float(x1),
                        y=float(y1),
                        width=float(x2 - x1),
                        height=float(y2 - y1),
                        track_id=int(tid) if tid is not None else None,
                    )
                )
        t_post = time.perf_counter()

        return InferenceResult(
            detections=detections,
            image_width=orig_w,
            image_height=orig_h,
            preprocess_ms=round((t_pre - t0) * 1000, 2),
            inference_ms=round((t_inf - t_pre) * 1000, 2),
            postprocess_ms=round((t_post - t_inf) * 1000, 2),
        )

    @property
    def class_names(self) -> dict[int, str]:
        return self._class_names

    def metadata(self) -> dict[str, Any]:
        return {
            "model_path": self.model_path,
            "device": self.device,
            "class_count": len(self._class_names),
            "classes": list(self._class_names.values()),
        }
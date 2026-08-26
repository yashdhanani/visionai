from __future__ import annotations

import time
from typing import Any

import numpy as np

from app.ml.inference import Detection, InferenceResult
from app.ml.yolo_model import YOLOModel, _to_bgr


class YOLOPoseModel(YOLOModel):
    def __init__(self, model_path: str, device: str = "auto"):
        super().__init__(model_path, device)

    def predict(
        self,
        image: np.ndarray,
        conf: float,
        iou: float,
        classes: list[int] | None = None,
        **kwargs,
    ) -> InferenceResult:
        if self._model is None:
            self.load()

        orig_h, orig_w = image.shape[:2]
        t0 = time.perf_counter()
        t_pre = t0

        results = self._model(
            _to_bgr(image),
            conf=conf,
            iou=iou,
            classes=classes,
            verbose=False,
        )
        t_inf = time.perf_counter()

        detections = []
        for r in results:
            if r.keypoints is None:
                continue
            # r.keypoints has .xy, .conf, .data
            # For each detection, we need to create a detection with keypoints
            boxes = r.boxes.xyxy.cpu().numpy() if r.boxes is not None else []
            confs = r.boxes.conf.cpu().numpy() if r.boxes is not None else []
            cls_ids = r.boxes.cls.cpu().numpy().astype(int) if r.boxes is not None else []
            kpts = r.keypoints.xy.cpu().numpy() if r.keypoints is not None else []

            for i, (box, cf, cid) in enumerate(zip(boxes, confs, cls_ids)):
                x1, y1, x2, y2 = box
                det = Detection(
                    class_id=int(cid),
                    class_name=self._class_names.get(int(cid), str(int(cid))),
                    confidence=float(cf),
                    x=float(x1),
                    y=float(y1),
                    width=float(x2 - x1),
                    height=float(y2 - y1),
                )
                # Attach keypoints as extra attribute
                if i < len(kpts):
                    det.keypoints = kpts[i].tolist()  # type: ignore
                detections.append(det)

        t_post = time.perf_counter()

        return InferenceResult(
            detections=detections,
            image_width=orig_w,
            image_height=orig_h,
            preprocess_ms=round((t_pre - t0) * 1000, 2),
            inference_ms=round((t_inf - t_pre) * 1000, 2),
            postprocess_ms=round((t_post - t_inf) * 1000, 2),
        )

    def predict_with_tracking(
        self,
        image: np.ndarray,
        conf: float,
        iou: float,
        tracker: str,
        persist: bool,
        classes: list[int] | None = None,
    ) -> InferenceResult:
        # For pose, tracking not supported in this simple version; fallback to predict
        return self.predict(image, conf, iou, classes)
from __future__ import annotations

import time
from typing import Any, Dict, List

from app.pipelines.base import VisionPipeline


class InspectionPipeline(VisionPipeline):
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.defect_classes = config.get("defect_classes", ["scratch", "crack", "missing_component"])
        self.results = []

    def preprocess(self, frame: Any) -> Any:
        return frame

    def infer(self, frame: Any, model: Any, **kwargs) -> Any:
        return model.predict(frame, **kwargs)

    def postprocess(self, result: Any) -> Any:
        return result

    def track(self, result: Any) -> Any:
        return result

    def create_events(self, result: Any, context: Dict = None) -> List[Dict]:
        events = []
        detections = result.detections if hasattr(result, "detections") else []
        for det in detections:
            if det.class_name in self.defect_classes:
                events.append({
                    "type": "defect_detected",
                    "defect_type": det.class_name,
                    "confidence": det.confidence,
                    "severity": "high" if det.confidence > 0.7 else "medium",
                    "result": "FAIL",
                    "timestamp": time.time(),
                })
        return events

    def format_result(self, result: Any) -> Dict:
        return {
            "defects_found": len(self.create_events(result)),
            "status": "FAIL" if self.create_events(result) else "PASS",
        }
from __future__ import annotations

import time
from typing import Any, Dict, List

from app.ml.inference import Detection
from app.pipelines.base import VisionPipeline


class SafetyPipeline(VisionPipeline):
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.ppe_classes = {
            "helmet": 0,   # placeholder, actual mapping depends on model
            "vest": 1,
            "gloves": 2,
        }
        self.violations: List[Dict] = []
        self.cooldown = 5.0  # seconds
        self.last_violation_time = 0.0

    def preprocess(self, frame: Any) -> Any:
        # No preprocessing needed beyond standard
        return frame

    def infer(self, frame: Any, model: Any, **kwargs) -> Any:
        # Run detection
        return model.predict(frame, **kwargs)

    def postprocess(self, result: Any) -> Any:
        return result

    def track(self, result: Any) -> Any:
        # For safety, we rely on tracking from model
        return result

    def create_events(self, result: Any, context: Dict = None) -> List[Dict]:
        events = []
        detections = result.detections if hasattr(result, "detections") else []
        now = time.time()

        # Check for PPE violations: if person detected without helmet/vest etc.
        persons = [d for d in detections if d.class_name == "person"]
        ppe_items = [d for d in detections if d.class_name in self.ppe_classes]

        # Simple rule: each person should have at least one PPE item nearby
        # For demo, just count violations
        if persons and not ppe_items and (now - self.last_violation_time > self.cooldown):
            events.append({
                "type": "safety_violation",
                "severity": "high",
                "description": "Person detected without PPE",
                "timestamp": now,
                "detections": [d.__dict__ for d in persons[:2]],
            })
            self.last_violation_time = now
            self.violations.append(events[-1])

        return events

    def format_result(self, result: Any) -> Dict:
        return {
            "violations": self.violations[-5:],
            "total_violations": len(self.violations),
        }
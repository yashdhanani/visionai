from __future__ import annotations

import time
from typing import Any, Dict, List

from app.pipelines.base import VisionPipeline


class FireSmokePipeline(VisionPipeline):
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.confirmation_frames = self.config.get("temporal_frames", 5)
        self.confidence_threshold = self.config.get("confidence", 0.5)
        self.history = []  # stores recent detections
        self.last_event_time = 0.0
        self.cooldown = 10.0

    def preprocess(self, frame: Any) -> Any:
        return frame

    def infer(self, frame: Any, model: Any, **kwargs) -> Any:
        # Expect model to detect fire/smoke classes
        return model.predict(frame, **kwargs)

    def postprocess(self, result: Any) -> Any:
        return result

    def track(self, result: Any) -> Any:
        return result

    def create_events(self, result: Any, context: Dict = None) -> List[Dict]:
        events = []
        detections = result.detections if hasattr(result, "detections") else []
        now = time.time()

        # Filter for fire/smoke classes (class names may vary)
        fire_smoke = [d for d in detections if d.class_name.lower() in ("fire", "smoke")]
        if fire_smoke:
            # Add to history
            self.history.append((now, fire_smoke))
            # Keep only recent history
            self.history = [h for h in self.history if now - h[0] < 10.0]

            # If we have enough consecutive frames with detection, confirm
            if len(self.history) >= self.confirmation_frames:
                # Check if cooldown has elapsed
                if now - self.last_event_time > self.cooldown:
                    events.append({
                        "type": "fire_smoke_detected",
                        "severity": "critical",
                        "description": f"{fire_smoke[0].class_name} detected for {len(self.history)} frames",
                        "timestamp": now,
                        "detections": [d.__dict__ for d in fire_smoke],
                        "confirmed": True,
                    })
                    self.last_event_time = now
                    self.history = []  # reset after event

        return events

    def format_result(self, result: Any) -> Dict:
        return {
            "fire_smoke_detected": len(self.history) > 0,
            "confirmation_progress": min(len(self.history) / self.confirmation_frames, 1.0),
        }
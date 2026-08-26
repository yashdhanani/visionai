from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple

import numpy as np

from app.pipelines.base import VisionPipeline


class ZonesPipeline(VisionPipeline):
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.zones = self.config.get("zones", [])  # list of polygons [[x1,y1], [x2,y2], ...]
        self.rules = self.config.get("rules", [])  # e.g., {"type": "intrusion", "zone_index": 0}
        self.track_history = {}  # track_id -> list of positions
        self.events = []
        self.cooldown = 2.0
        self.last_event_time = 0.0

    def preprocess(self, frame: Any) -> Any:
        return frame

    def infer(self, frame: Any, model: Any, **kwargs) -> Any:
        return model.predict(frame, **kwargs)

    def postprocess(self, result: Any) -> Any:
        return result

    def track(self, result: Any) -> Any:
        # Update track history
        detections = result.detections if hasattr(result, "detections") else []
        for det in detections:
            if det.track_id is not None:
                if det.track_id not in self.track_history:
                    self.track_history[det.track_id] = []
                # Store center point
                cx = det.x + det.width / 2
                cy = det.y + det.height / 2
                self.track_history[det.track_id].append((cx, cy))
                # Keep last 50 positions
                if len(self.track_history[det.track_id]) > 50:
                    self.track_history[det.track_id].pop(0)
        return result

    def _point_in_polygon(self, point: Tuple[float, float], polygon: List[Tuple[float, float]]) -> bool:
        x, y = point
        n = len(polygon)
        inside = False
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def create_events(self, result: Any, context: Dict = None) -> List[Dict]:
        events = []
        detections = result.detections if hasattr(result, "detections") else []
        now = time.time()

        if not self.zones:
            return events

        for det in detections:
            if det.track_id is None:
                continue
            cx = det.x + det.width / 2
            cy = det.y + det.height / 2
            for idx, zone in enumerate(self.zones):
                if self._point_in_polygon((cx, cy), zone):
                    # Check for intrusion rules
                    for rule in self.rules:
                        if rule.get("type") == "intrusion" and rule.get("zone_index") == idx:
                            if now - self.last_event_time > self.cooldown:
                                events.append({
                                    "type": "zone_intrusion",
                                    "zone": f"Zone {idx+1}",
                                    "track_id": det.track_id,
                                    "timestamp": now,
                                    "confidence": det.confidence,
                                })
                                self.last_event_time = now
                                break
        return events

    def format_result(self, result: Any) -> Dict:
        return {
            "active_zones": len(self.zones),
            "tracked_objects": len(self.track_history),
        }
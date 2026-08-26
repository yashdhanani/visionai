from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
from app.ml.inference import Detection

logger = logging.getLogger("visionai.tracking")


class Tracker:
    def __init__(self, tracker_type: str = "bytetrack", **kwargs):
        self.tracker_type = tracker_type
        self.trackers: dict[int, dict] = {}
        self.next_id = 1

    def update(self, detections: list[Detection], frame_id: int) -> list[Detection]:
        # Simplified tracking: assign new IDs to detections that are close to existing ones
        # In production, this would use a proper algorithm like ByteTrack or BoT-SORT
        tracked = []
        for det in detections:
            if det.track_id is not None:
                # If the model already provides a track_id, use it
                tracked.append(det)
                continue
            # Simple heuristic: assign new ID
            det.track_id = self.next_id
            self.next_id += 1
            tracked.append(det)
        return tracked


class TrackingManager:
    _instance: Optional[TrackingManager] = None

    def __new__(cls) -> TrackingManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.trackers: dict[str, Tracker] = {}
        self._initialized = True

    def get_tracker(self, tracker_type: str = "bytetrack") -> Tracker:
        if tracker_type not in self.trackers:
            self.trackers[tracker_type] = Tracker(tracker_type)
        return self.trackers[tracker_type]

    def reset(self, tracker_type: str | None = None):
        if tracker_type is None:
            self.trackers.clear()
        elif tracker_type in self.trackers:
            del self.trackers[tracker_type]


def get_tracking_manager() -> TrackingManager:
    return TrackingManager()
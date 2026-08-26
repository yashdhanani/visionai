from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from app.ml.inference import Detection


@dataclass
class CountingState:
    current: int = 0
    entered: int = 0
    exited: int = 0
    peak: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "current": self.current,
            "entered": self.entered,
            "exited": self.exited,
            "peak": self.peak,
        }


class PeopleCounter:
    def __init__(self, line_y: float = 0.5, cooldown: float = 1.0):
        self.line_y = line_y
        self.cooldown = cooldown
        self.track_state: dict[int, dict] = {}
        self.state = CountingState()

    def update(self, detections: list[Detection], frame_height: int, now: float) -> CountingState:
        # Reset peak if needed
        if self.state.current > self.state.peak:
            self.state.peak = self.state.current

        # Process each detection with track_id
        active_tracks = set()
        for det in detections:
            if det.track_id is None:
                continue
            tid = det.track_id
            active_tracks.add(tid)
            # Get current bbox center y (normalized)
            cy = det.y + det.height / 2
            norm_y = cy / frame_height

            if tid not in self.track_state:
                self.track_state[tid] = {
                    "last_y": norm_y,
                    "last_update": now,
                    "entered": False,
                    "exited": False,
                }
            else:
                ts = self.track_state[tid]
                # If cooldown not elapsed, skip
                if now - ts["last_update"] < self.cooldown:
                    continue
                prev_y = ts["last_y"]
                # Crossing logic: if crossed line from top to bottom -> entered? From bottom to top -> exited?
                # Assuming line_y is the threshold; if prev_y < line_y and norm_y >= line_y -> entered
                if prev_y < self.line_y <= norm_y and not ts["entered"]:
                    self.state.current += 1
                    self.state.entered += 1
                    ts["entered"] = True
                    ts["exited"] = False
                elif prev_y > self.line_y and norm_y <= self.line_y and not ts["exited"]:
                    self.state.current -= 1
                    if self.state.current < 0:
                        self.state.current = 0
                    self.state.exited += 1
                    ts["exited"] = True
                    ts["entered"] = False
                ts["last_y"] = norm_y
                ts["last_update"] = now

        # Remove tracks that are no longer active
        for tid in list(self.track_state.keys()):
            if tid not in active_tracks:
                del self.track_state[tid]

        return self.state
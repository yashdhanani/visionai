from __future__ import annotations

import time
from typing import Any, Dict, List

from app.pipelines.base import VisionPipeline


class TrafficSignalPipeline(VisionPipeline):
    """Adaptive traffic-signal control.

    Counts tracked vehicles per approach (zone), estimates demand share and
    computes green times with a queue-proportional adaptation of Webster's
    cycle-length method. Phases advance in wall-clock time and emit
    `signal_phase_change` events.

    If no zones are configured, the frame is split into 4 quadrant approaches
    (North/South/East/West) so the pipeline works out of the box.
    """

    VEHICLE_CLASSES = {"car", "motorcycle", "bus", "truck", "bicycle", "train"}

    def __init__(self, config: Dict[str, Any] | None = None):
        cfg = config or {}
        # zones: [{"name": "North", "points": [[x, y], ...]}, ...]
        self.zones: List[Dict[str, Any]] = cfg.get("zones") or []
        self.lost_time_per_phase: float = float(cfg.get("lost_time", 3.0))
        self.min_green: float = float(cfg.get("min_green", 7.0))
        self.max_green: float = float(cfg.get("max_green", 60.0))
        self.min_cycle: float = float(cfg.get("min_cycle", 30.0))
        self.max_cycle: float = float(cfg.get("max_cycle", 150.0))
        self.seconds_per_vehicle: float = float(cfg.get("seconds_per_vehicle", 2.5))
        self.smoothing_frames: int = int(cfg.get("smoothing_frames", 10))

        self.count_history: List[Dict[int, float]] = []
        self.current_phase: int = 0
        self.phase_started_at: float = time.time()
        self._last_plan: Dict[str, Any] | None = None
        self.events: List[Dict[str, Any]] = []

    # ── geometry helpers ────────────────────────────────────────────────
    @staticmethod
    def _point_in_polygon(point: tuple[float, float], polygon: List[List[float]]) -> bool:
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

    def _approaches_for_frame(self, width: int, height: int) -> List[Dict[str, Any]]:
        if self.zones:
            return self.zones
        # Default: 4 quadrant approaches for an intersection view
        hw, hh = width / 2, height / 2
        return [
            {"name": "North", "points": [[0, 0], [width, 0], [width, hh], [0, hh]]},
            {"name": "East", "points": [[hw, 0], [width, 0], [width, height], [hw, height]]},
            {"name": "South", "points": [[0, hh], [width, hh], [width, height], [0, height]]},
            {"name": "West", "points": [[0, 0], [hw, 0], [hw, height], [0, height]]},
        ]

    # ── pipeline stages ─────────────────────────────────────────────────
    def preprocess(self, frame: Any) -> Any:
        return frame

    def infer(self, frame: Any, model: Any, **kwargs) -> Any:
        return model.predict(frame, **kwargs)

    def postprocess(self, result: Any) -> Any:
        return result

    def track(self, result: Any) -> Any:
        detections = getattr(result, "detections", []) or []
        approaches = self._approaches_for_frame(
            getattr(result, "image_width", 640), getattr(result, "image_height", 480)
        )
        counts: Dict[int, float] = {i: 0.0 for i in range(len(approaches))}
        for det in detections:
            if det.class_name not in self.VEHICLE_CLASSES:
                continue
            cx = det.x + det.width / 2
            cy = det.y + det.height / 2
            for i, zone in enumerate(approaches):
                if self._point_in_polygon((cx, cy), zone["points"]):
                    counts[i] += 1
                    break
        self.count_history.append(counts)
        if len(self.count_history) > self.smoothing_frames:
            self.count_history.pop(0)
        return result

    # ── signal timing core ──────────────────────────────────────────────
    def _smoothed_demand(self, n: int) -> List[float]:
        demand = [0.0] * n
        if not self.count_history:
            return demand
        for snap in self.count_history:
            for i in range(n):
                demand[i] += snap.get(i, 0.0)
        k = len(self.count_history)
        return [round(d / k, 2) for d in demand]

    def _compute_plan(self, demand: List[float]) -> Dict[str, Any]:
        n = len(demand)
        total = sum(demand)
        if total <= 0:
            shares = [1.0 / n] * n
        else:
            shares = [d / total for d in demand]

        # Cycle length grows with total demand (Webster-adapted, queue-proportional)
        cycle = self.min_cycle + self.seconds_per_vehicle * total
        cycle = max(self.min_cycle, min(self.max_cycle, cycle))

        lost_total = self.lost_time_per_phase * n
        green_total = max(cycle - lost_total, self.min_green * n)

        greens = [green_total * s for s in shares]
        greens = [max(self.min_green, min(self.max_green, g)) for g in greens]

        # Renormalize after clamping so the plan sums to green_total
        scale = green_total / sum(greens) if sum(greens) > 0 else 1.0
        greens = [round(g * scale, 1) for g in greens]

        return {
            "cycle_length": round(cycle, 1),
            "lost_time_total": round(lost_total, 1),
            "green_times": greens,
            "demand_shares": [round(s, 3) for s in shares],
        }

    def _advance_phase_if_due(self, greens: List[float]) -> None:
        elapsed = time.time() - self.phase_started_at
        active = [g for g in greens if g > 0]
        if not active:
            return
        idx = self.current_phase % len(greens)
        if elapsed >= greens[idx]:
            self.current_phase = (self.current_phase + 1) % len(greens)
            self.phase_started_at = time.time()
            self.events.append({
                "type": "signal_phase_change",
                "phase_index": self.current_phase,
                "green_time": greens[self.current_phase],
                "timestamp": time.time(),
            })

    def create_events(self, result: Any, context: Dict | None = None) -> List[Dict]:
        events, self.events = self.events, []
        return events

    def format_result(self, result: Any) -> Dict:
        approaches = self._approaches_for_frame(
            getattr(result, "image_width", 640), getattr(result, "image_height", 480)
        )
        n = len(approaches)
        demand = self._smoothed_demand(n)
        plan = self._compute_plan(demand)
        greens = plan["green_times"]
        self._advance_phase_if_due(greens)

        elapsed = time.time() - self.phase_started_at
        remaining = max(0.0, greens[self.current_phase % n] - elapsed)

        return {
            "method": "queue_proportional_webster_adapted",
            "cycle_length": plan["cycle_length"],
            "total_vehicles": round(sum(demand), 1),
            "current_phase": self.current_phase % n,
            "phase_time_remaining": round(remaining, 1),
            "approaches": [
                {
                    "name": approaches[i].get("name", f"Approach {i + 1}"),
                    "vehicles": demand[i],
                    "share": plan["demand_shares"][i],
                    "green_time": greens[i],
                    "phase_index": i,
                }
                for i in range(n)
            ],
        }
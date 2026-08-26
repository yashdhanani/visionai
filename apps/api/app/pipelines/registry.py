from __future__ import annotations

import time
from typing import Any, Dict, List, Type

from app.pipelines.base import VisionPipeline
from app.pipelines.safety import SafetyPipeline
from app.pipelines.fire_smoke import FireSmokePipeline
from app.pipelines.zones import ZonesPipeline
from app.pipelines.inspection import InspectionPipeline
from app.pipelines.traffic_signal import TrafficSignalPipeline


class CountingPipeline(VisionPipeline):
    def __init__(self, config: Dict[str, Any] | None = None):
        from app.pipelines.counting import PeopleCounter
        self.counter = PeopleCounter(line_y=(config or {}).get("line_y", 0.5))

    def preprocess(self, frame: Any) -> Any:
        return frame

    def infer(self, frame: Any, model: Any, **kwargs) -> Any:
        return model.predict(frame, **kwargs)

    def postprocess(self, result: Any) -> Any:
        return result

    def track(self, result: Any) -> Any:
        return result

    def create_events(self, result: Any, context: Dict | None = None) -> List[Dict]:
        return []

    def format_result(self, result: Any) -> Dict:
        detections = result.detections if hasattr(result, "detections") else []
        height = result.image_height if hasattr(result, "image_height") else 480
        state = self.counter.update(detections, height, time.time())
        return state.to_dict()


PIPELINE_REGISTRY: Dict[str, Type[VisionPipeline]] = {
    "counting": CountingPipeline,
    "safety": SafetyPipeline,
    "fire_smoke": FireSmokePipeline,
    "zones": ZonesPipeline,
    "inspection": InspectionPipeline,
    "traffic_analysis": TrafficSignalPipeline,
}


def get_pipeline(category: str, config: Dict[str, Any] | None = None) -> VisionPipeline | None:
    pipeline_cls = PIPELINE_REGISTRY.get(category)
    if pipeline_cls is None:
        return None
    try:
        return pipeline_cls(config or {})
    except Exception:
        return None
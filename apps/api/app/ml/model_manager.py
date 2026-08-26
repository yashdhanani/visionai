from __future__ import annotations

import logging
import os
import threading
from typing import Any

from app.config.settings import settings
from app.ml.inference import DetectionModel
from app.ml.yolo_model import YOLOModel

logger = logging.getLogger("visionai.ml.manager")


class ModelManager:
    _instance: ModelManager | None = None
    _lock = threading.Lock()

    def __new__(cls) -> ModelManager:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._models: dict[str, DetectionModel] = {}
        self._active_model_id: str | None = None
        self._initialized = True

    def register(self, model_id: str, model: DetectionModel) -> None:
        self._models[model_id] = model

    def get(self, model_id: str | None = None) -> DetectionModel | None:
        if model_id is None:
            model_id = self._active_model_id
        if model_id is None:
            return None
        return self._models.get(model_id)

    def set_active(self, model_id: str) -> bool:
        if model_id in self._models:
            self._active_model_id = model_id
            logger.info(f"Active model set to {model_id}")
            return True
        return False

    def _resolve_model_path(self, name: str) -> str:
        if not name:
            return name
        if os.path.isabs(name) and os.path.exists(name):
            return name
        ml_dir = os.path.dirname(os.path.abspath(__file__))
        api_dir = os.path.abspath(os.path.join(ml_dir, "..", ".."))
        project_root = os.path.abspath(os.path.join(api_dir, ".."))
        candidates = [
            os.path.join(api_dir, name),
            os.path.join(ml_dir, name),
            os.path.join(project_root, name),
            os.path.join(project_root, "apps", "api", name),
            os.path.join(os.getcwd(), name),
            os.path.join(os.getcwd(), "apps", "api", name),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return name

    def load_default(self) -> DetectionModel:
        model_id = "default"
        if model_id in self._models:
            return self._models[model_id]

        path = settings.MODEL_PATH or settings.MODEL_NAME
        path = self._resolve_model_path(path)
        model = YOLOModel(path, settings.MODEL_DEVICE)
        model.load()
        model.warmup((640, 640))
        self.register(model_id, model)
        self._active_model_id = model_id
        return model

    def load_face(self) -> DetectionModel:
        model_id = "face"
        if model_id in self._models:
            return self._models[model_id]

        path = self._resolve_model_path(settings.FACE_MODEL_NAME)
        model = YOLOModel(path, settings.MODEL_DEVICE)
        model.load()
        model.warmup((640, 640))
        self.register(model_id, model)
        logger.info(f"Face model loaded: {path}")
        return model

    def load_plate(self) -> DetectionModel:
        model_id = "plate"
        if model_id in self._models:
            return self._models[model_id]

        path = self._resolve_model_path(settings.PLATE_MODEL_NAME)
        model = YOLOModel(path, settings.MODEL_DEVICE)
        model.load()
        model.warmup((640, 640))
        self.register(model_id, model)
        logger.info(f"Plate model loaded: {path}")
        return model

    def load_pose(self) -> DetectionModel:
        model_id = "pose"
        if model_id in self._models:
            return self._models[model_id]

        from app.ml.yolo_pose import YOLOPoseModel

        path = self._resolve_model_path(settings.POSE_MODEL_NAME)
        model = YOLOPoseModel(path, settings.MODEL_DEVICE)
        model.load()
        model.warmup((640, 640))
        self.register(model_id, model)
        logger.info(f"Pose model loaded: {path}")
        return model

    def load_fire_smoke(self) -> DetectionModel:
        model_id = "fire_smoke"
        if model_id in self._models:
            return self._models[model_id]

        path = self._resolve_model_path(settings.FIRE_SMOKE_MODEL_NAME)
        model = YOLOModel(path, settings.MODEL_DEVICE)
        model.load()
        model.warmup((640, 640))
        self.register(model_id, model)
        logger.info(f"Fire/Smoke model loaded: {path}")
        return model

    def list_metadata(self) -> dict[str, Any]:
        return {mid: m.metadata() for mid, m in self._models.items()}

    def list_available(self) -> list[dict[str, str]]:
        return [
            {"id": "default", "name": "YOLOv8n (General)", "classes": "80 classes (COCO)"},
            {"id": "face", "name": "YOLOv8n-Face", "classes": "1 class (face)"},
            {"id": "plate", "name": "YOLOv8m-Plate", "classes": "1 class (license plate)"},
            {"id": "pose", "name": "YOLOv8n-Pose", "classes": "1 class (person, 17 keypoints)"},
            {"id": "fire_smoke", "name": "YOLOv8n-FireSmoke (D-Fire)", "classes": "2 classes (fire, smoke)"},
        ]


def get_model_manager() -> ModelManager:
    return ModelManager()


def get_active_model() -> DetectionModel:
    mgr = get_model_manager()
    model = mgr.get()
    if model is None:
        model = mgr.load_default()
    return model


def get_model_by_id(model_id: str) -> DetectionModel:
    mgr = get_model_manager()
    model = mgr.get(model_id)
    if model is None:
        if model_id == "face":
            model = mgr.load_face()
        elif model_id == "plate":
            model = mgr.load_plate()
        elif model_id == "pose":
            model = mgr.load_pose()
        elif model_id == "fire_smoke":
            model = mgr.load_fire_smoke()
        elif model_id == "default":
            model = mgr.load_default()
        else:
            model = mgr.get()
            if model is None:
                model = mgr.load_default()
    return model

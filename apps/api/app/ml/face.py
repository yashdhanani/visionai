from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
from app.ml.model_manager import get_model_by_id

logger = logging.getLogger("visionai.face")


class FaceEmbedding:
    def __init__(self, model_id: str = "face"):
        self.model_id = model_id
        self._model = None

    def load(self):
        if self._model is None:
            self._model = get_model_by_id(self.model_id)
        return self._model

    def detect_faces(self, image: np.ndarray, conf: float = 0.35) -> List[Dict[str, Any]]:
        model = self.load()
        if model is None:
            return []
        result = model.predict(image, conf, 0.45, classes=None)
        faces = []
        for det in result.detections:
            faces.append({
                "bbox": {"x": det.x, "y": det.y, "width": det.width, "height": det.height},
                "confidence": det.confidence,
            })
        return faces

    def embed(self, face_crop: np.ndarray) -> np.ndarray:
        # Placeholder: in production, use a face recognition model like Facenet or ArcFace
        # For now, return a random vector
        return np.random.randn(128).astype(np.float32)

    def verify(self, embedding1: np.ndarray, embedding2: np.ndarray, threshold: float = 0.6) -> bool:
        # Placeholder: cosine similarity
        dot = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        if norm1 == 0 or norm2 == 0:
            return False
        similarity = dot / (norm1 * norm2)
        return similarity >= threshold


class FaceProfile:
    def __init__(self, user_id: str, name: str, embedding: np.ndarray):
        self.user_id = user_id
        self.name = name
        self.embedding = embedding


class AttendanceManager:
    def __init__(self):
        self.profiles: Dict[str, FaceProfile] = {}
        self.embedder = FaceEmbedding()

    def enroll(self, user_id: str, name: str, face_crop: np.ndarray) -> bool:
        embedding = self.embedder.embed(face_crop)
        self.profiles[user_id] = FaceProfile(user_id, name, embedding)
        return True

    def verify(self, face_crop: np.ndarray, threshold: float = 0.6) -> Optional[FaceProfile]:
        embedding = self.embedder.embed(face_crop)
        best_match = None
        best_score = -1
        for profile in self.profiles.values():
            if self.embedder.verify(embedding, profile.embedding, threshold):
                score = float(np.dot(embedding, profile.embedding) / (np.linalg.norm(embedding) * np.linalg.norm(profile.embedding)))
                if score > best_score:
                    best_score = score
                    best_match = profile
        return best_match


_attendance_manager = AttendanceManager()


def get_attendance_manager() -> AttendanceManager:
    return _attendance_manager
from __future__ import annotations

import base64
import io
import json
import logging
import time
import uuid
from typing import Any, Dict, Set

from fastapi import WebSocket, WebSocketDisconnect

import numpy as np


class _NumpyEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

import numpy as np
import cv2
from fastapi import WebSocket, WebSocketDisconnect
from PIL import Image
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.db.session import SessionLocal
from app.ml.inference import Detection
from app.ml.model_manager import get_active_model, get_model_by_id
from app.models.db_models import Detection as DBDetection, DetectionObject, DetectionSession, Project, SourceType
from app.services.storage_service import get_storage, generate_object_key

logger = logging.getLogger("visionai.ws")

# Connection manager with limits
_active_connections: Dict[str, Set[WSConnection]] = {}
_max_connections_per_ip = 5  # Max concurrent WS connections per client IP


def _get_client_ip(websocket: WebSocket) -> str:
    """Extract client IP from WebSocket connection."""
    return websocket.client.host if websocket.client else "unknown"


def _check_connection_limit(websocket: WebSocket) -> bool:
    """Check if client has not exceeded max concurrent connections."""
    ip = _get_client_ip(websocket)
    current_count = len(_active_connections.get(ip, set()))
    if current_count >= _max_connections_per_ip:
        return False
    return True


def _add_connection(ip: str, conn: WSConnection) -> None:
    """Track a new WebSocket connection."""
    if ip not in _active_connections:
        _active_connections[ip] = set()
    _active_connections[ip].add(conn)


def _remove_connection(ip: str, conn: WSConnection) -> None:
    """Remove a WebSocket connection from tracking."""
    conns = _active_connections.get(ip)
    if conns:
        conns.discard(conn)
        if not conns:
            del _active_connections[ip]


class WSConnection:
    def __init__(self, websocket: WebSocket, user_id: str, project_id: str, category: str = "objects"):
        self.ws = websocket
        self.user_id = user_id
        self.project_id = project_id
        self.category = category
        self.session_id = uuid.uuid4().hex
        self.model = None
        self.conf = 0.35
        self.iou = 0.45
        self.classes: list[int] | None = None
        self.tracker: str | None = None
        self.persist = False
        self.max_fps = 30
        self.resolution = (640, 360)
        self.quality = 80
        self.last_frame_time = 0.0
        self.seq = 0
        self.frame_count = 0
        self.detection_count = 0
        self.start_time = time.time()
        self._pipeline = None
        self.pipeline_config: dict = {}

        # Register connection with limits
        ip = _get_client_ip(websocket)
        if _check_connection_limit(websocket):
            _add_connection(ip, self)
        else:
            # Exceeded connection limit
            import asyncio
            asyncio.create_task(self._reject_connection(websocket))
            raise WebSocketDisclosure("Max connections exceeded")

    def _get_category_class_filter(self) -> list[int] | None:
        COCO_PERSON = [0]
        COCO_VEHICLES = [1, 2, 3, 5, 7]
        if self.category in ("people", "counting", "pose"):
            return COCO_PERSON
        if self.category in ("vehicles", "traffic_analysis"):
            return COCO_VEHICLES
        if self.category == "fire_smoke":
            return None  # fire/smoke model has its own classes
        return None

    async def handle(self) -> None:
        await self.ws.accept()
        model_id = self.ws.query_params.get("model", None)
        if not model_id:
            from app.categories.registry import get_category
            cat = get_category(self.category)
            if cat:
                model_id = cat.default_model_id
        self.model = get_model_by_id(model_id) if model_id else get_active_model()
        if self.model is None:
            await self.ws.close(code=4002, reason="Model unavailable")
            return

        await self.send_json({
            "type": "connected",
            "session_id": self.session_id,
            "category": self.category,
            "model_id": model_id or "default",
            "model_info": self.model.metadata(),
        })

        try:
            while True:
                msg = await self.ws.receive_text()
                await self.process_message(msg)
        except WebSocketDisconnect:
            pass
        finally:
            await self.finalize()

    async def process_message(self, raw: str) -> None:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            await self.send_error("INVALID_JSON", "Invalid JSON message")
            return

        msg_type = data.get("type")

        if msg_type == "config":
            self.conf = data.get("confidence", self.conf)
            self.iou = data.get("iou", self.iou)
            self.tracker = data.get("tracker")
            self.persist = self.tracker is not None and self.tracker != "off"
            self.max_fps = min(data.get("max_fps", self.max_fps), settings.MAX_WEBSOCKET_FPS)
            res_str = data.get("resolution", "640x360")
            w, h = map(int, res_str.split("x"))
            self.resolution = (w, h)
            self.quality = max(10, min(data.get("quality", self.quality), 95))
            new_model_id = data.get("model_id")
            if new_model_id:
                new_model = get_model_by_id(new_model_id)
                if new_model:
                    self.model = new_model
                    if new_model_id in ("face", "plate", "fire_smoke", "pose"):
                        self.classes = None
                    else:
                        self.classes = self._get_category_class_filter()
            elif not self.classes:
                self.classes = self._get_category_class_filter()
            if "zones" in data and isinstance(data["zones"], list):
                self.pipeline_config["zones"] = data["zones"]
            await self.send_json({"type": "processing", "message": "Configuration updated"})

        elif msg_type == "start":
            await self.send_json({"type": "processing", "message": "Detection started"})

        elif msg_type == "frame":
            await self.handle_frame(data)

        elif msg_type == "heartbeat":
            await self.send_json({"type": "heartbeat", "ts": int(time.time() * 1000)})

        elif msg_type == "stop":
            await self.send_json({"type": "processing", "message": "Detection stopped"})

    async def handle_frame(self, data: dict) -> None:
        now = time.perf_counter()
        min_interval = 1.0 / self.max_fps
        if now - self.last_frame_time < min_interval:
            # Rate-limited: acknowledge so request/response clients never hang
            await self.send_json({"type": "frame_skipped", "reason": "rate_limit"})
            return
        self.last_frame_time = now

        jpeg_b64 = data.get("jpeg_b64")
        if not jpeg_b64:
            await self.send_error("MISSING_FRAME", "Missing frame data")
            return

        try:
            img_bytes = base64.b64decode(jpeg_b64)
            nparr = np.frombuffer(img_bytes, np.uint8)
            bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if bgr is None:
                raise ValueError("imdecode failed")
            frame = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        except Exception as exc:
            await self.send_error("INVALID_FRAME", f"Cannot decode frame: {exc}")
            return

        self.seq += 1
        seq = self.seq
        ts = int(time.time() * 1000)

        loop = None
        try:
            import asyncio
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass

        try:
            if self.tracker and self.tracker != "off":
                res = await loop.run_in_executor(
                    None,
                    lambda: self.model.predict_with_tracking(frame, self.conf, self.iou, self.tracker, self.persist, self.classes),
                )
            else:
                res = await loop.run_in_executor(
                    None,
                    lambda: self.model.predict(frame, self.conf, self.iou, self.classes),
                )
        except Exception as exc:
            logger.exception("Inference error")
            await self.send_error("INFERENCE_ERROR", str(exc))
            return

        from app.ml.enhance import enhance_detections

        detections = enhance_detections(
            res.detections, frame, res.image_width, res.image_height, self.conf, self.iou
        )
        self.frame_count += 1
        self.detection_count += len(detections)

        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0

        perf = {
            "fps": round(fps, 1),
            "latency_ms": round((time.perf_counter() - now) * 1000, 1),
            "preprocess_ms": res.preprocess_ms,
            "inference_ms": res.inference_ms,
            "postprocess_ms": res.postprocess_ms,
        }

        # Apply category-specific pipeline if available (never crash detection on pipeline errors)
        category_data = None
        events = []
        try:
            if self._pipeline is None:
                from app.pipelines.registry import get_pipeline
                self._pipeline = get_pipeline(self.category, self.pipeline_config)
            if self._pipeline:
                self._pipeline.track(res)
                events = self._pipeline.create_events(res, {"timestamp": time.time()}) or []
                category_data = self._pipeline.format_result(res)
        except Exception:
            logger.exception("Pipeline error (detection continues)")

        out = {
            "type": "detection",
            "category": self.category,
            "seq": seq,
            "ts": ts,
            "detections": [
                {
                    "class_id": d.class_id,
                    "class_name": d.class_name,
                    "confidence": d.confidence,
                    "bbox": {"x": d.x, "y": d.y, "width": d.width, "height": d.height},
                    "track_id": d.track_id,
                    "text": getattr(d, "text", None),
                    **({"keypoints": d.keypoints} if getattr(d, "keypoints", None) else {}),
                }
                for d in detections
            ],
            "performance": perf,
            "frame_width": res.image_width,
            "frame_height": res.image_height,
            "count": len(detections),
            "category_data": category_data,
            "events": events,
        }
        await self.send_json(out)

    async def send_json(self, obj: dict) -> None:
        await self.ws.send_text(json.dumps(obj, cls=_NumpyEncoder))

    async def send_error(self, code: str, message: str) -> None:
        await self.send_json({"type": "error", "code": code, "message": message})

    async def _reject_connection(self, websocket: WebSocket) -> None:
        """Reject WebSocket connection due to limit exceeded."""
        try:
            await websocket.close(code=4003, reason="Max concurrent connections exceeded")
        except Exception:
            pass

    async def finalize(self) -> None:
        db = SessionLocal()
        try:
            from datetime import datetime, timezone
            from app.models.db_models import Project

            wall_end = time.time()
            elapsed = wall_end - self.start_time
            avg_fps = self.frame_count / elapsed if elapsed > 0 else 0

            project_id = self.project_id or None
            if not project_id:
                # Keep real session history: assign the user's first project,
                # creating a default one if needed (existing table has NOT NULL).
                project = db.query(Project).filter(Project.user_id == self.user_id).first()
                if project is None:
                    project = Project(user_id=self.user_id, name="Live Sessions")
                    db.add(project)
                    db.flush()
                project_id = project.id

            session = DetectionSession(
                project_id=project_id,
                source_type=SourceType.WEBCAM,
                started_at=datetime.fromtimestamp(self.start_time, tz=timezone.utc),
                ended_at=datetime.fromtimestamp(wall_end, tz=timezone.utc),
                avg_fps=round(avg_fps, 1),
                total_frames=self.frame_count,
                total_detections=self.detection_count,
            )
            db.add(session)
            db.commit()
            logger.info(f"Session persisted: {self.frame_count} frames, {self.detection_count} detections")
        except Exception:
            logger.exception("Failed to persist WS session")
        finally:
            db.close()
            # Unregister connection
            ip = _get_client_ip(self.ws)
            _remove_connection(ip, self)
from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")
user_id_ctx: ContextVar[str] = ContextVar("user_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
            "user_id": user_id_ctx.get(),
        }
        for key in ("endpoint", "processing_time_ms", "model", "inference_time_ms", "status", "error"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info and record.exc_info[0]:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class PrettyFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        rid = request_id_ctx.get()
        base = f"{self.formatTime(record, '%H:%M:%S')} {record.levelname:<7} [{rid[:8]}] {record.getMessage()}"
        if record.exc_info and record.exc_info[0]:
            base += "\n" + self.formatException(record.exc_info)
        return base


def setup_logging(env: str = "development") -> None:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if env == "development" else logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if env == "production" else PrettyFormatter())
    root.handlers = [handler]
    for noisy in ("uvicorn.access", "uvicorn.error", "ultralytics", "fontTools", "matplotlib", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


logger = logging.getLogger("visionai")

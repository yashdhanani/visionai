from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

import logging

logger = logging.getLogger("visionai.events")


@dataclass
class Event:
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    event_type: str = ""
    category: str = ""
    camera_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float = 0.0
    entities: list[dict] = field(default_factory=list)
    snapshot: str = ""
    metadata: dict = field(default_factory=dict)


class EventEngine:
    def __init__(self):
        self._listeners: list[Callable[[Event], None]] = []

    def subscribe(self, listener: Callable[[Event], None]) -> None:
        self._listeners.append(listener)

    def emit(self, event: Event) -> None:
        logger.info(f"Event emitted: {event.event_type} ({event.event_id})")
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                logger.exception(f"Listener failed: {e}")

    def create_event(self, event_type: str, category: str, camera_id: str = "", confidence: float = 0.0,
                     entities: list[dict] = None, snapshot: str = "", metadata: dict = None) -> Event:
        return Event(
            event_type=event_type,
            category=category,
            camera_id=camera_id,
            confidence=confidence,
            entities=entities or [],
            snapshot=snapshot,
            metadata=metadata or {},
        )


_event_engine = EventEngine()


def get_event_engine() -> EventEngine:
    return _event_engine
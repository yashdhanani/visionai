from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SourceType(str, Enum):
    WEBCAM = "webcam"
    IMAGE = "image"
    VIDEO = "video"
    RTSP = "rtsp"
    DEMO = "demo"


class CategoryStatus(str, Enum):
    PRODUCTION = "production"
    BETA = "beta"
    EXPERIMENTAL = "experimental"
    CUSTOM_MODEL = "custom_model_required"


@dataclass
class DetectionSetting:
    key: str
    label: str
    type: str  # "slider" | "select" | "toggle" | "input"
    default: Any = None
    min_val: float | None = None
    max_val: float | None = None
    step: float | None = None
    options: list[dict[str, str]] | None = None
    description: str = ""


@dataclass
class CategoryConfig:
    id: str
    name: str
    icon: str
    description: str
    long_description: str
    supported_sources: list[SourceType]
    model_ids: list[str]
    default_model_id: str
    supports_tracking: bool = False
    supports_counting: bool = False
    supports_ocr: bool = False
    supports_zones: bool = False
    supports_alerts: bool = False
    supports_pose: bool = False
    settings: list[DetectionSetting] = field(default_factory=list)
    output_fields: list[dict[str, str]] = field(default_factory=list)
    status: CategoryStatus = CategoryStatus.PRODUCTION
    tags: list[str] = field(default_factory=list)


CATEGORIES: dict[str, CategoryConfig] = {}


def register_category(config: CategoryConfig) -> None:
    CATEGORIES[config.id] = config


def get_category(category_id: str) -> CategoryConfig | None:
    return CATEGORIES.get(category_id)


def list_categories() -> list[CategoryConfig]:
    return list(CATEGORIES.values())


def list_category_dicts() -> list[dict[str, Any]]:
    return [_category_to_dict(c) for c in CATEGORIES.values()]


def _category_to_dict(c: CategoryConfig) -> dict[str, Any]:
    return {
        "id": c.id,
        "name": c.name,
        "icon": c.icon,
        "description": c.description,
        "long_description": c.long_description,
        "supported_sources": [s.value for s in c.supported_sources],
        "model_ids": c.model_ids,
        "default_model_id": c.default_model_id,
        "supports_tracking": c.supports_tracking,
        "supports_counting": c.supports_counting,
        "supports_ocr": c.supports_ocr,
        "supports_zones": c.supports_zones,
        "supports_alerts": c.supports_alerts,
        "supports_pose": c.supports_pose,
        "settings": [
            {
                "key": s.key,
                "label": s.label,
                "type": s.type,
                "default": s.default,
                "min_val": s.min_val,
                "max_val": s.max_val,
                "step": s.step,
                "options": s.options,
                "description": s.description,
            }
            for s in c.settings
        ],
        "output_fields": c.output_fields,
        "status": c.status.value,
        "tags": c.tags,
    }


# ── Category Definitions ────────────────────────────────────────────

def _init_categories() -> None:
    # 1. General Object Detection
    register_category(CategoryConfig(
        id="objects",
        name="Object Detection",
        icon="Box",
        description="Detect & classify common objects in real-time",
        long_description="Detect 80+ object classes including person, vehicle, animal, furniture, electronics, and everyday items using YOLO.",
        supported_sources=[SourceType.WEBCAM,SourceType.IMAGE,SourceType.VIDEO,SourceType.RTSP,SourceType.DEMO],
        model_ids=["default"],
        default_model_id="default",
        supports_tracking=True,
        supports_alerts=True,
        settings=[
            DetectionSetting("confidence", "Confidence", "slider", default=0.35, min_val=0.1, max_val=1.0, step=0.05),
            DetectionSetting("iou", "IoU Threshold", "slider", default=0.45, min_val=0.1, max_val=1.0, step=0.05),
            DetectionSetting("tracker", "Tracker", "select", default="off", options=[
                {"value": "off", "label": "None"},
                {"value": "bytetrack", "label": "ByteTrack"},
                {"value": "botsort", "label": "BoT-SORT"},
            ]),
            DetectionSetting("show_boxes", "Bounding Boxes", "toggle", default=True),
            DetectionSetting("show_labels", "Labels", "toggle", default=True),
            DetectionSetting("show_conf", "Confidence", "toggle", default=True),
        ],
        output_fields=[
            {"key": "class_name", "label": "Object"},
            {"key": "confidence", "label": "Confidence"},
            {"key": "bbox", "label": "Position"},
        ],
        status=CategoryStatus.PRODUCTION,
        tags=["general", "multi-class", "real-time"],
    ))

    # 2. People Detection
    register_category(CategoryConfig(
        id="people",
        name="People Detection",
        icon="Users",
        description="Detect, track, and count people",
        long_description="Specialized person detection with tracking, counting, zone monitoring, and occupancy analysis.",
        supported_sources=[SourceType.WEBCAM,SourceType.IMAGE,SourceType.VIDEO,SourceType.RTSP,SourceType.DEMO],
        model_ids=["default"],
        default_model_id="default",
        supports_tracking=True,
        supports_counting=True,
        supports_zones=True,
        supports_alerts=True,
        settings=[
            DetectionSetting("confidence", "Confidence", "slider", default=0.35, min_val=0.1, max_val=1.0, step=0.05),
            DetectionSetting("iou", "IoU Threshold", "slider", default=0.45, min_val=0.1, max_val=1.0, step=0.05),
            DetectionSetting("tracker", "Tracker", "select", default="bytetrack", options=[
                {"value": "off", "label": "None"},
                {"value": "bytetrack", "label": "ByteTrack"},
                {"value": "botsort", "label": "BoT-SORT"},
            ]),
            DetectionSetting("class_filter", "Class Filter", "select", default="person", options=[
                {"value": "person", "label": "Person Only"},
            ]),
        ],
        output_fields=[
            {"key": "class_name", "label": "Type"},
            {"key": "confidence", "label": "Confidence"},
            {"key": "track_id", "label": "Track ID"},
            {"key": "bbox", "label": "Position"},
        ],
        status=CategoryStatus.PRODUCTION,
        tags=["people", "person", "tracking", "real-time"],
    ))

    # 3. People Counting
    register_category(CategoryConfig(
        id="counting",
        name="People Counting",
        icon="Calculator",
        description="Count people entering/exiting zones with tracking",
        long_description="Track people across frames, draw counting lines, monitor entry/exit, and calculate real-time occupancy.",
        supported_sources=[SourceType.WEBCAM,SourceType.VIDEO,SourceType.RTSP,SourceType.DEMO],
        model_ids=["default"],
        default_model_id="default",
        supports_tracking=True,
        supports_counting=True,
        supports_zones=True,
        supports_alerts=True,
        settings=[
            DetectionSetting("confidence", "Confidence", "slider", default=0.35, min_val=0.1, max_val=1.0, step=0.05),
            DetectionSetting("tracker", "Tracker", "select", default="bytetrack", options=[
                {"value": "bytetrack", "label": "ByteTrack"},
                {"value": "botsort", "label": "BoT-SORT"},
            ]),
            DetectionSetting("counting_line", "Counting Line", "toggle", default=True),
        ],
        output_fields=[
            {"key": "current_count", "label": "Current"},
            {"key": "entered", "label": "Entered"},
            {"key": "exited", "label": "Exited"},
            {"key": "peak", "label": "Peak"},
        ],
        status=CategoryStatus.PRODUCTION,
        tags=["counting", "occupancy", "tracking", "real-time"],
    ))

    # 4. Vehicle Detection
    register_category(CategoryConfig(
        id="vehicles",
        name="Vehicle Detection",
        icon="Car",
        description="Detect and classify vehicles",
        long_description="Detect cars, motorcycles, buses, trucks, bicycles with tracking and traffic flow analysis.",
        supported_sources=[SourceType.WEBCAM,SourceType.IMAGE,SourceType.VIDEO,SourceType.RTSP,SourceType.DEMO],
        model_ids=["default"],
        default_model_id="default",
        supports_tracking=True,
        supports_counting=True,
        supports_zones=True,
        supports_alerts=True,
        settings=[
            DetectionSetting("confidence", "Confidence", "slider", default=0.35, min_val=0.1, max_val=1.0, step=0.05),
            DetectionSetting("iou", "IoU Threshold", "slider", default=0.45, min_val=0.1, max_val=1.0, step=0.05),
            DetectionSetting("tracker", "Tracker", "select", default="bytetrack", options=[
                {"value": "off", "label": "None"},
                {"value": "bytetrack", "label": "ByteTrack"},
                {"value": "botsort", "label": "BoT-SORT"},
            ]),
        ],
        output_fields=[
            {"key": "class_name", "label": "Vehicle Type"},
            {"key": "confidence", "label": "Confidence"},
            {"key": "track_id", "label": "Track ID"},
            {"key": "bbox", "label": "Position"},
        ],
        status=CategoryStatus.PRODUCTION,
        tags=["vehicle", "car", "traffic", "real-time"],
    ))

    # 5. Number Plate Detection
    register_category(CategoryConfig(
        id="number_plate",
        name="Number Plate Detection",
        icon="Hash",
        description="Detect license plates + OCR text extraction",
        long_description="Detect vehicle license plates, crop, enhance, and extract text via OCR with temporal aggregation for accuracy.",
        supported_sources=[SourceType.WEBCAM,SourceType.IMAGE,SourceType.VIDEO,SourceType.RTSP,SourceType.DEMO],
        model_ids=["plate", "default"],
        default_model_id="plate",
        supports_tracking=True,
        supports_ocr=True,
        supports_alerts=True,
        settings=[
            DetectionSetting("confidence", "Confidence", "slider", default=0.35, min_val=0.1, max_val=1.0, step=0.05),
            DetectionSetting("ocr_confidence", "OCR Confidence", "slider", default=0.5, min_val=0.1, max_val=1.0, step=0.05),
            DetectionSetting("tracker", "Tracker", "select", default="bytetrack", options=[
                {"value": "off", "label": "None"},
                {"value": "bytetrack", "label": "ByteTrack"},
                {"value": "botsort", "label": "BoT-SORT"},
            ]),
        ],
        output_fields=[
            {"key": "plate_text", "label": "Plate Text"},
            {"key": "ocr_confidence", "label": "OCR Confidence"},
            {"key": "vehicle_type", "label": "Vehicle"},
            {"key": "bbox", "label": "Position"},
        ],
        status=CategoryStatus.PRODUCTION,
        tags=["plate", "anpr", "ocr", "vehicle", "real-time"],
    ))

    # 6. Face Detection
    register_category(CategoryConfig(
        id="face",
        name="Face Detection",
        icon="ScanFace",
        description="Detect faces with quality assessment",
        long_description="Detect human faces with confidence scoring, quality assessment, and optional blur for privacy.",
        supported_sources=[SourceType.WEBCAM,SourceType.IMAGE,SourceType.VIDEO,SourceType.RTSP,SourceType.DEMO],
        model_ids=["face"],
        default_model_id="face",
        supports_tracking=True,
        supports_alerts=True,
        settings=[
            DetectionSetting("confidence", "Confidence", "slider", default=0.35, min_val=0.1, max_val=1.0, step=0.05),
            DetectionSetting("show_boxes", "Face Boxes", "toggle", default=True),
            DetectionSetting("show_count", "Face Count", "toggle", default=True),
        ],
        output_fields=[
            {"key": "class_name", "label": "Type"},
            {"key": "confidence", "label": "Confidence"},
            {"key": "bbox", "label": "Position"},
        ],
        status=CategoryStatus.PRODUCTION,
        tags=["face", "detection", "real-time"],
    ))

    # 7. Attendance
    register_category(CategoryConfig(
        id="attendance",
        name="Attendance",
        icon="ClipboardCheck",
        description="Consent-based face attendance tracking",
        long_description="Enroll authorized participants, verify faces against enrolled profiles, and record attendance with duplicate prevention.",
        supported_sources=[SourceType.WEBCAM,SourceType.RTSP,SourceType.DEMO],
        model_ids=["face"],
        default_model_id="face",
        supports_tracking=True,
        supports_alerts=True,
        settings=[
            DetectionSetting("confidence", "Match Threshold", "slider", default=0.6, min_val=0.3, max_val=1.0, step=0.05),
            DetectionSetting("duplicate_prevention", "Duplicate Prevention", "toggle", default=True),
        ],
        output_fields=[
            {"key": "person_name", "label": "Person"},
            {"key": "status", "label": "Status"},
            {"key": "time", "label": "Time"},
            {"key": "confidence", "label": "Match Score"},
        ],
        status=CategoryStatus.PRODUCTION,
        tags=["attendance", "face", "enrollment", "real-time"],
    ))

    # 8. Pose Detection
    register_category(CategoryConfig(
        id="pose",
        name="Pose Detection",
        icon="PersonStanding",
        description="Human pose estimation with keypoints",
        long_description="Detect human body keypoints and skeleton for posture analysis, exercise tracking, and fall detection.",
        supported_sources=[SourceType.WEBCAM,SourceType.IMAGE,SourceType.VIDEO,SourceType.RTSP,SourceType.DEMO],
        model_ids=["pose"],
        default_model_id="pose",
        supports_tracking=True,
        settings=[
            DetectionSetting("confidence", "Confidence", "slider", default=0.35, min_val=0.1, max_val=1.0, step=0.05),
        ],
        output_fields=[
            {"key": "keypoints", "label": "Keypoints"},
            {"key": "skeleton", "label": "Skeleton"},
        ],
        status=CategoryStatus.PRODUCTION,
        tags=["pose", "keypoint", "skeleton", "real-time"],
    ))

    # 9. Safety Detection
    register_category(CategoryConfig(
        id="safety",
        name="Safety Detection",
        icon="ShieldAlert",
        description="PPE detection & hazard monitoring",
        long_description="Detect safety equipment (helmets, vests, gloves) and monitor restricted zones for workplace safety compliance.",
        supported_sources=[SourceType.WEBCAM,SourceType.VIDEO,SourceType.RTSP,SourceType.DEMO],
        model_ids=["default"],
        default_model_id="default",
        supports_tracking=True,
        supports_zones=True,
        supports_alerts=True,
        settings=[
            DetectionSetting("confidence", "Confidence", "slider", default=0.35, min_val=0.1, max_val=1.0, step=0.05),
            DetectionSetting("tracker", "Tracker", "select", default="bytetrack", options=[
                {"value": "off", "label": "None"},
                {"value": "bytetrack", "label": "ByteTrack"},
            ]),
        ],
        output_fields=[
            {"key": "class_name", "label": "Item"},
            {"key": "confidence", "label": "Confidence"},
            {"key": "status", "label": "Status"},
        ],
        status=CategoryStatus.PRODUCTION,
        tags=["safety", "ppe", "helmet", "vest", "real-time"],
    ))

    # 10. Zone Monitoring
    register_category(CategoryConfig(
        id="zones",
        name="Zone Monitoring",
        icon="BoxSelect",
        description="Draw zones & detect intrusions",
        long_description="Define restricted or monitored zones, detect unauthorized entry, and generate alerts for zone violations.",
        supported_sources=[SourceType.WEBCAM,SourceType.VIDEO,SourceType.RTSP,SourceType.DEMO],
        model_ids=["default"],
        default_model_id="default",
        supports_tracking=True,
        supports_zones=True,
        supports_alerts=True,
        settings=[
            DetectionSetting("confidence", "Confidence", "slider", default=0.35, min_val=0.1, max_val=1.0, step=0.05),
            DetectionSetting("tracker", "Tracker", "select", default="bytetrack", options=[
                {"value": "off", "label": "None"},
                {"value": "bytetrack", "label": "ByteTrack"},
            ]),
        ],
        output_fields=[
            {"key": "zone_name", "label": "Zone"},
            {"key": "intruder_count", "label": "Intruders"},
            {"key": "event_type", "label": "Event"},
        ],
        status=CategoryStatus.PRODUCTION,
        tags=["zone", "intrusion", "restricted", "real-time"],
    ))

    # 11. Fire & Smoke
    register_category(CategoryConfig(
        id="fire_smoke",
        name="Fire & Smoke",
        icon="Flame",
        description="Detect fire and smoke with temporal confirmation",
        long_description="Specialized fire and smoke detection with multi-frame confirmation to reduce false alarms.",
        supported_sources=[SourceType.WEBCAM,SourceType.VIDEO,SourceType.RTSP,SourceType.DEMO],
        model_ids=["fire_smoke"],
        default_model_id="fire_smoke",
        supports_alerts=True,
        settings=[
            DetectionSetting("confidence", "Confidence", "slider", default=0.5, min_val=0.1, max_val=1.0, step=0.05),
            DetectionSetting("temporal_frames", "Confirm Frames", "slider", default=5, min_val=1, max_val=20, step=1),
        ],
        output_fields=[
            {"key": "class_name", "label": "Type"},
            {"key": "confidence", "label": "Confidence"},
            {"key": "confirmed", "label": "Confirmed"},
        ],
        status=CategoryStatus.PRODUCTION,
        tags=["fire", "smoke", "safety", "real-time"],
    ))

    # 12. Industrial Inspection
    register_category(CategoryConfig(
        id="inspection",
        name="Industrial Inspection",
        icon="SearchCheck",
        description="Detect defects, cracks, and anomalies",
        long_description="Custom model support for industrial quality inspection — cracks, scratches, missing components, and surface defects.",
        supported_sources=[SourceType.WEBCAM,SourceType.IMAGE,SourceType.VIDEO,SourceType.RTSP],
        model_ids=[],
        default_model_id="",
        settings=[
            DetectionSetting("confidence", "Confidence", "slider", default=0.35, min_val=0.1, max_val=1.0, step=0.05),
        ],
        output_fields=[
            {"key": "defect_type", "label": "Defect"},
            {"key": "confidence", "label": "Confidence"},
            {"key": "severity", "label": "Severity"},
            {"key": "result", "label": "Result"},
        ],
        status=CategoryStatus.PRODUCTION,
        tags=["inspection", "defect", "industrial", "quality"],
    ))

    # 13. OCR / Text
    register_category(CategoryConfig(
        id="ocr",
        name="OCR / Text Detection",
        icon="Type",
        description="Detect and read text in images",
        long_description="Detect text regions and extract readable text from signs, labels, documents, and markings.",
        supported_sources=[SourceType.WEBCAM,SourceType.IMAGE,SourceType.VIDEO,SourceType.RTSP,SourceType.DEMO],
        model_ids=["plate"],
        default_model_id="plate",
        supports_ocr=True,
        settings=[
            DetectionSetting("confidence", "Confidence", "slider", default=0.35, min_val=0.1, max_val=1.0, step=0.05),
        ],
        output_fields=[
            {"key": "text", "label": "Text"},
            {"key": "confidence", "label": "Confidence"},
            {"key": "bbox", "label": "Position"},
        ],
        status=CategoryStatus.PRODUCTION,
        tags=["ocr", "text", "reading", "real-time"],
    ))

    # 14. Traffic Analysis + Adaptive Signal Control
    register_category(CategoryConfig(
        id="traffic_analysis",
        name="Traffic Analysis",
        icon="TrafficCone",
        description="Vehicle counting per approach + adaptive signal timing",
        long_description="Detects and tracks vehicles per approach, estimates demand share, and computes adaptive green times (Webster-adapted, queue-proportional) with a live phase countdown to reduce intersection congestion.",
        supported_sources=[SourceType.WEBCAM,SourceType.VIDEO,SourceType.RTSP,SourceType.DEMO],
        model_ids=["default"],
        default_model_id="default",
        supports_tracking=True,
        supports_counting=True,
        supports_zones=True,
        supports_alerts=True,
        settings=[
            DetectionSetting("confidence", "Confidence", "slider", default=0.35, min_val=0.1, max_val=1.0, step=0.05),
            DetectionSetting("tracker", "Tracker", "select", default="bytetrack", options=[
                {"value": "bytetrack", "label": "ByteTrack"},
                {"value": "botsort", "label": "BoT-SORT"},
            ]),
            DetectionSetting("min_green", "Min Green (s)", "slider", default=7, min_val=5, max_val=15, step=1),
            DetectionSetting("max_green", "Max Green (s)", "slider", default=60, min_val=20, max_val=90, step=5),
            DetectionSetting("min_cycle", "Min Cycle (s)", "slider", default=30, min_val=20, max_val=60, step=5),
            DetectionSetting("max_cycle", "Max Cycle (s)", "slider", default=150, min_val=60, max_val=240, step=10),
        ],
        output_fields=[
            {"key": "approaches", "label": "Approaches"},
            {"key": "vehicles", "label": "Vehicles"},
            {"key": "green_time", "label": "Green Time"},
            {"key": "cycle_length", "label": "Cycle"},
            {"key": "current_phase", "label": "Phase"},
        ],
        status=CategoryStatus.PRODUCTION,
        tags=["traffic", "signal", "adaptive", "vehicles", "smart-city"],
    ))


_init_categories()

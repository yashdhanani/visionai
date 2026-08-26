from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def gen_uuid() -> str:
    return uuid.uuid4().hex


class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class SourceType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    WEBCAM = "webcam"
    STREAM = "stream"


class DetectionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ModelStatus(str, enum.Enum):
    AVAILABLE = "available"
    ACTIVE = "active"
    DISABLED = "disabled"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    projects: Mapped[list[Project]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    api_keys: Mapped[list[ApiKey]] = relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner: Mapped[User] = relationship(back_populates="projects")
    detections: Mapped[list[Detection]] = relationship(back_populates="project", cascade="all, delete-orphan")
    sessions: Mapped[list[DetectionSession]] = relationship(back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_projects_user_created", "user_id", "created_at"),)


class MLModel(TimestampMixin, Base):
    __tablename__ = "ml_models"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(160))
    version: Mapped[str] = mapped_column(String(40), default="1.0")
    framework: Mapped[str] = mapped_column(String(60), default="ultralytics-yolo")
    path: Mapped[str] = mapped_column(String(500))
    status: Mapped[ModelStatus] = mapped_column(Enum(ModelStatus), default=ModelStatus.AVAILABLE, index=True)
    accuracy_map: Mapped[float | None] = mapped_column(Float, nullable=True)
    classes_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    inference_speed_fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    detections: Mapped[list[Detection]] = relationship(back_populates="model")


class Detection(TimestampMixin, Base):
    __tablename__ = "detections"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    model_id: Mapped[str | None] = mapped_column(ForeignKey("ml_models.id", ondelete="SET NULL"), nullable=True)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), index=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    original_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    annotated_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    processing_time_ms: Mapped[float | None] = mapped_column(Float)
    inference_time_ms: Mapped[float | None] = mapped_column(Float)
    fps: Mapped[float | None] = mapped_column(Float)
    object_count: Mapped[int] = mapped_column(Integer, default=0, index=True)
    avg_confidence: Mapped[float | None] = mapped_column(Float)
    image_width: Mapped[int | None] = mapped_column(Integer)
    image_height: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[DetectionStatus] = mapped_column(
        Enum(DetectionStatus), default=DetectionStatus.COMPLETED, index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress: Mapped[float] = mapped_column(Float, default=100.0)
    frames_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    frames_done: Mapped[int | None] = mapped_column(Integer, nullable=True)

    project: Mapped[Project] = relationship(back_populates="detections")
    model: Mapped[MLModel | None] = relationship(back_populates="detections")
    objects: Mapped[list[DetectionObject]] = relationship(
        back_populates="detection", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_detections_project_created", "project_id", "created_at"),
        Index("ix_detections_source_status", "source_type", "status"),
    )


class DetectionObject(Base):
    __tablename__ = "detection_objects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    detection_id: Mapped[str] = mapped_column(ForeignKey("detections.id", ondelete="CASCADE"), index=True)
    class_id: Mapped[int] = mapped_column(Integer, index=True)
    class_name: Mapped[str] = mapped_column(String(80), index=True)
    confidence: Mapped[float] = mapped_column(Float, index=True)
    x: Mapped[float] = mapped_column(Float)
    y: Mapped[float] = mapped_column(Float)
    width: Mapped[float] = mapped_column(Float)
    height: Mapped[float] = mapped_column(Float)
    track_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    text: Mapped[str | None] = mapped_column(String(64), nullable=True)

    detection: Mapped[Detection] = relationship(back_populates="objects")

    __table_args__ = (Index("ix_objects_detection_class", "detection_id", "class_name"),)


class DetectionSession(Base):
    __tablename__ = "detection_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_uuid)
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=True
    )
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    avg_fps: Mapped[float | None] = mapped_column(Float)
    total_frames: Mapped[int] = mapped_column(Integer, default=0)
    total_detections: Mapped[int] = mapped_column(Integer, default=0)

    project: Mapped[Project] = relationship(back_populates="sessions")


class ApiKey(TimestampMixin, Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    key_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    prefix_display: Mapped[str] = mapped_column(String(40))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    user: Mapped[User] = relationship(back_populates="api_keys")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class AuthEvent(Base):
    __tablename__ = "auth_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    event: Mapped[str] = mapped_column(String(60), index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(300))
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class OneTimeToken(Base):
    """Architecture for password-reset and email-verification flows."""

    __tablename__ = "one_time_tokens"

    token_hash: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    purpose: Mapped[str] = mapped_column(String(30), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

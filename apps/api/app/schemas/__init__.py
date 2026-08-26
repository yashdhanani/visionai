from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Envelope(BaseModel):
    success: bool
    meta: dict[str, str] = Field(default_factory=dict)


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorEnvelope(BaseModel):
    success: Literal[False] = False
    error: ErrorDetail


class DataEnvelope(BaseModel):
    success: Literal[True] = True
    data: Any


class UserBase(BaseModel):
    name: NonEmptyStr = Field(max_length=120)
    email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")


class UserCreate(UserBase):
    password: Annotated[str, StringConstraints(min_length=8, max_length=128)]


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(UserBase):
    id: str
    avatar: str | None
    role: Literal["USER", "ADMIN"]
    email_verified: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int


class ApiKeyCreate(BaseModel):
    name: NonEmptyStr = Field(max_length=120)


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    prefix_display: str
    created_at: datetime
    last_used_at: datetime | None
    revoked: bool


class ProjectBase(BaseModel):
    name: NonEmptyStr = Field(max_length=160)
    description: str | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: NonEmptyStr | None = Field(default=None, max_length=160)
    description: str | None = None


class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class ModelBase(BaseModel):
    name: NonEmptyStr = Field(max_length=160)
    version: str = Field(default="1.0", max_length=40)
    path: NonEmptyStr = Field(max_length=500)


class ModelCreate(ModelBase):
    pass


class ModelResponse(ModelBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    framework: str
    status: Literal["available", "active", "disabled"]
    accuracy_map: float | None
    classes_count: int | None
    inference_speed_fps: float | None
    created_at: datetime | None


class BBox(BaseModel):
    x: float
    y: float
    width: float
    height: float


class DetectionObjectIn(BaseModel):
    class_id: int
    class_name: str
    confidence: float = Field(ge=0, le=1)
    bbox: BBox
    track_id: int | None = None
    text: str | None = None


class DetectionObjectOut(DetectionObjectIn):
    id: int = 0

    model_config = ConfigDict(from_attributes=True)


class DetectionBase(BaseModel):
    source_type: Literal["image", "video", "webcam", "stream"]
    model_id: str | None = None


class ImageDetectionResponse(DetectionBase):
    id: str
    project_id: str
    source_url: str | None
    original_path: str | None
    annotated_path: str | None
    processing_time_ms: float | None
    inference_time_ms: float | None
    fps: float | None
    object_count: int
    avg_confidence: float | None
    image_width: int | None
    image_height: int | None
    status: Literal["pending", "processing", "completed", "failed"]
    objects: list[DetectionObjectOut]
    created_at: datetime


class DetectionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    source_type: Literal["image", "video", "webcam", "stream"]
    model_id: str | None
    object_count: int
    avg_confidence: float | None
    processing_time_ms: float | None
    fps: float | None
    status: Literal["pending", "processing", "completed", "failed"]
    created_at: datetime


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
    pages: int


class VideoJobStatus(BaseModel):
    detection_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    progress: float
    frames_total: int | None
    frames_done: int | None
    fps: float | None
    objects_detected: int
    eta_seconds: int | None
    error: str | None


class DetectionOut(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: BBox
    track_id: int | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: Annotated[str, StringConstraints(min_length=8, max_length=128)]


class OneTimeTokenRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: Annotated[str, StringConstraints(min_length=8, max_length=128)]


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    checks: dict[str, Literal["ok", "down"]]

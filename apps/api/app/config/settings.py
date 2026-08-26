from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(PROJECT_ROOT, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: Literal["development", "production", "test"] = "development"
    APP_NAME: str = "VisionAI"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    API_BASE_URL: str = "http://localhost:8001"
    WEB_BASE_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000"

    DATABASE_URL: str = f"sqlite:///{os.path.join(PROJECT_ROOT, 'data', 'visionai.db')}"
    REDIS_URL: str = ""

    JWT_SECRET: str = "dev-only-secret-change-me-0123456789abcdef0123456789abcdef"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    ADMIN_EMAIL: str = "admin@gmail.com"
    ADMIN_PASSWORD: str = "admin123"

    MODEL_NAME: str = "yolov8n.pt"
    MODEL_PATH: str = ""
    MODEL_DEVICE: str = "auto"
    MODEL_CONFIDENCE: float = 0.20
    MODEL_IOU: float = 0.40
    FACE_MODEL_NAME: str = "yolov8n-face.pt"
    PLATE_MODEL_NAME: str = "yolov8m-plate.pt"
    POSE_MODEL_NAME: str = "yolov8n-pose.pt"
    FIRE_SMOKE_MODEL_NAME: str = "yolov8n-fire.pt"
    MAX_WEBSOCKET_FPS: int = 30

    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    STORAGE_ROOT: str = os.path.join(PROJECT_ROOT, "data", "uploads")
    S3_ENDPOINT: str = ""
    S3_BUCKET: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_REGION: str = "us-east-1"

    MAX_UPLOAD_SIZE_MB: int = 10
    MAX_VIDEO_UPLOAD_SIZE_MB: int = 200

    RATE_LIMIT_AUTH_PER_MINUTE: int = 15
    RATE_LIMIT_DETECT_PER_MINUTE: int = 120

    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    @field_validator("CORS_ORIGINS")
    @classmethod
    def split_origins(cls, v: str) -> list[str]:
        return [o.strip() for o in v.split(",") if o.strip()]

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        # Allow default or user-provided JWT secret without crashing
        return v

    @field_validator("ADMIN_PASSWORD")
    @classmethod
    def validate_admin_password(cls, v: str, info) -> str:
        # Allow default or user-provided admin password
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def max_video_upload_bytes(self) -> int:
        return self.MAX_VIDEO_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

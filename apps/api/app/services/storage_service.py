from __future__ import annotations

import hashlib
import mimetypes
import os
import uuid
from pathlib import Path

from app.config.settings import settings


class StorageBackend:
    def save(self, key: str, data: bytes, content_type: str) -> str: ...
    def load(self, key: str) -> bytes | None: ...
    def delete(self, key: str) -> bool: ...
    def url(self, key: str, ttl: int = 3600) -> str: ...


class LocalStorage(StorageBackend):
    def __init__(self, root: str) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe_key = key.replace("..", "").lstrip("/")
        resolved = (self.root / safe_key).resolve()
        if not str(resolved).startswith(str(self.root)):
            raise ValueError(f"Path traversal detected: {key}")
        return resolved

    def save(self, key: str, data: bytes, content_type: str) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def load(self, key: str) -> bytes | None:
        path = self._path(key)
        return path.read_bytes() if path.exists() else None

    def delete(self, key: str) -> bool:
        path = self._path(key)
        if path.exists():
            path.unlink()
            return True
        return False

    def url(self, key: str, ttl: int = 3600) -> str:
        return f"/api/v1/files/{key}"


class S3Storage(StorageBackend):
    def __init__(self) -> None:
        try:
            import boto3
        except ImportError:
            raise RuntimeError("boto3 not installed")
        if not all([settings.S3_ENDPOINT, settings.S3_BUCKET, settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY]):
            raise RuntimeError("S3 settings incomplete")
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
        )
        self.bucket = settings.S3_BUCKET

    def save(self, key: str, data: bytes, content_type: str) -> str:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return key

    def load(self, key: str) -> bytes | None:
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=key)
            return obj["Body"].read()
        except self.client.exceptions.NoSuchKey:
            return None

    def delete(self, key: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    def url(self, key: str, ttl: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=ttl
        )


_storage: StorageBackend | None = None


def get_storage() -> StorageBackend:
    global _storage
    if _storage is not None:
        return _storage
    if settings.STORAGE_BACKEND == "s3":
        _storage = S3Storage()
    else:
        _storage = LocalStorage(settings.STORAGE_ROOT)
    return _storage


def generate_object_key(user_id: str, filename: str, prefix: str = "uploads") -> str:
    ext = Path(filename).suffix.lower() or ".bin"
    safe = hashlib.md5(filename.encode()).hexdigest()[:8]
    return f"{prefix}/{user_id}/{uuid.uuid4().hex[:12]}_{safe}{ext}"


def validate_upload(filename: str, content: bytes, max_size: int) -> tuple[bool, str | None]:
    if len(content) > max_size:
        return False, f"File size {len(content)} exceeds limit {max_size}"
    mime, _ = mimetypes.guess_type(filename)
    allowed = {"image/jpeg", "image/png", "image/webp", "video/mp4", "video/webm", "video/quicktime", "application/octet-stream"}
    if mime and mime not in allowed:
        return False, f"Unsupported MIME type: {mime}"
    ext = Path(filename).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".webm", ".mov", ".pt"}:
        return False, f"Unsupported extension: {ext}"
    return True, None
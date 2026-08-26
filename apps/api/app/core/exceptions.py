from __future__ import annotations


class AppError(Exception):
    status_code = 400
    code = "BAD_REQUEST"

    def __init__(self, message: str = "Bad request", *, code: str | None = None, status_code: int | None = None):
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)


class ValidationError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"


class UnauthorizedError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message)


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"


class RateLimitError(AppError):
    status_code = 429
    code = "RATE_LIMIT_EXCEEDED"

    def __init__(self, message: str = "Too many requests, slow down"):
        super().__init__(message)


class InvalidFileError(AppError):
    status_code = 400
    code = "INVALID_FILE"


class ModelUnavailableError(AppError):
    status_code = 503
    code = "MODEL_UNAVAILABLE"

    def __init__(self, message: str = "Inference model is unavailable"):
        super().__init__(message)


class StorageError(AppError):
    status_code = 500
    code = "STORAGE_ERROR"


class InferenceError(AppError):
    status_code = 500
    code = "INFERENCE_ERROR"

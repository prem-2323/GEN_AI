"""Centralized application exception hierarchy."""
from __future__ import annotations

from typing import Any, Dict, Optional


class AppException(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class DocumentValidationError(AppException):
    """Raised when an uploaded document fails format, size, or integrity checks."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, status_code=422, details=details)


class ExtractionError(AppException):
    """Raised when document content extraction fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, status_code=500, details=details)


class ProcessingError(AppException):
    """Raised when a processing pipeline, analysis, or transformation step fails."""

    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, status_code=status_code, details=details)


class ConfigurationError(AppException):
    """Raised when application or environment configuration is invalid."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, status_code=500, details=details)


class ResourceNotFoundError(AppException):
    """Raised when a requested resource (project, source, deliverable) does not exist."""

    def __init__(self, resource_type: str, resource_id: str) -> None:
        message = f"{resource_type} '{resource_id}' not found."
        super().__init__(message=message, status_code=404, details={"resourceType": resource_type, "resourceId": resource_id})


class UnauthorizedError(AppException):
    """Raised when authentication credentials are missing or invalid."""

    def __init__(self, message: str = "Authentication required.") -> None:
        super().__init__(message=message, status_code=401)


class ForbiddenError(AppException):
    """Raised when an authenticated user does not have permission for the resource."""

    def __init__(self, message: str = "Access forbidden.") -> None:
        super().__init__(message=message, status_code=403)


class ConflictError(AppException):
    """Raised when a resource state conflict occurs."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, status_code=409, details=details)


class PreconditionFailedError(AppException):
    """Raised when a precondition check fails (e.g., approval required before export)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, status_code=412, details=details)

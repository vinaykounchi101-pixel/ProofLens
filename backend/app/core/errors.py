"""Domain exceptions and centralized HTTP error response formatting."""

from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class ProofLensException(Exception):
    """Base exception for all ProofLens domain errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class ResourceNotFoundException(ProofLensException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ValidationException(ProofLensException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_FAILED",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class UnprocessablePDFException(ProofLensException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="UNPROCESSABLE_PDF",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class QuotaExhaustedException(ProofLensException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="QUOTA_EXHAUSTED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
        )


class ProviderUnavailableException(ProofLensException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="PROVIDER_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


async def prooflens_exception_handler(request: Request, exc: ProofLensException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "req_unknown")
    payload = {
        "error_code": exc.error_code,
        "message": exc.message,
        "details": exc.details,
        "request_id": request_id,
    }
    return JSONResponse(status_code=exc.status_code, content=payload)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "req_unknown")
    payload = {
        "error_code": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected server error occurred. Please try again later.",
        "details": {},
        "request_id": request_id,
    }
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)

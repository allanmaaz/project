from fastapi import HTTPException, status


class ClarifyBaseError(Exception):
    """Base error class for all Clarify AI exceptions."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class UploadTooLargeError(ClarifyBaseError):
    def __init__(self, size_mb: float, limit_mb: int):
        super().__init__(
            f"File size {size_mb:.1f}MB exceeds the {limit_mb}MB limit.",
            "UPLOAD_TOO_LARGE"
        )


class UnsupportedFileTypeError(ClarifyBaseError):
    def __init__(self, mime_type: str):
        super().__init__(
            f"File type '{mime_type}' is not supported. "
            "Upload JPG, PNG, WEBP, HEIC, or PDF files.",
            "UNSUPPORTED_FILE_TYPE"
        )


class AnalysisFailedError(ClarifyBaseError):
    def __init__(self, reason: str = ""):
        super().__init__(
            f"Analysis could not be completed. {reason}".strip(),
            "ANALYSIS_FAILED"
        )


class LLMUnavailableError(ClarifyBaseError):
    def __init__(self):
        super().__init__(
            "AI service is temporarily unavailable. Your file is saved — try again in a moment.",
            "LLM_UNAVAILABLE"
        )


class RateLimitError(ClarifyBaseError):
    def __init__(self, upgrade: bool = True):
        msg = "You've reached your upload limit for this hour."
        if upgrade:
            msg += " Upgrade to Pro for unlimited access."
        super().__init__(msg, "RATE_LIMIT_EXCEEDED")


class UploadLimitError(ClarifyBaseError):
    def __init__(self, limit: int):
        super().__init__(
            f"You've used all {limit} uploads for this month on the free plan. "
            "Upgrade to Pro for unlimited uploads.",
            "MONTHLY_LIMIT_REACHED"
        )


class NotFoundError(ClarifyBaseError):
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found.", "NOT_FOUND")


class ForbiddenError(ClarifyBaseError):
    def __init__(self):
        super().__init__("You don't have permission to access this resource.", "FORBIDDEN")


class AuthError(ClarifyBaseError):
    def __init__(self, detail: str = "Authentication required."):
        super().__init__(detail, "UNAUTHORIZED")


# ── HTTP exception helpers ──────────────────────────────────────────────────

def raise_http(error: ClarifyBaseError, status_code: int) -> None:
    raise HTTPException(
        status_code=status_code,
        detail={"code": error.code, "message": error.message},
    )

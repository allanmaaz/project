from pydantic import BaseModel
from datetime import datetime
import uuid


class UploadStatusResponse(BaseModel):
    upload_id: str
    status: str           # pending | processing | completed | failed
    step: str | None = None       # ocr | classification | analysis | done
    progress_percent: int = 0
    error: str | None = None


class UploadCreateResponse(BaseModel):
    upload_id: str
    status: str = "pending"
    estimated_seconds: int = 10


class UploadListItem(BaseModel):
    id: str
    auto_title: str | None
    document_type: str | None
    detected_language: str
    risk_level: str | None
    risk_score: int
    urgency: str | None
    status: str
    thumbnail_url: str | None
    original_filename: str | None
    file_type: str
    file_size_bytes: int
    created_at: datetime

    class Config:
        from_attributes = True


class UploadListResponse(BaseModel):
    items: list[UploadListItem]
    total: int
    page: int
    per_page: int

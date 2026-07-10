from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    avatar_url: str | None
    plan: str
    preferred_language: str
    ui_language: str
    theme: str
    uploads_this_month: int
    total_uploads: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None
    preferred_language: str | None = None
    ui_language: str | None = None
    theme: str | None = None


class UserStatsResponse(BaseModel):
    total_uploads: int
    uploads_this_month: int
    plan: str
    plan_limit: int
    uploads_remaining: int
    spending_total_this_month: float
    spending_by_category: dict
    document_types_breakdown: list[dict]
    risk_breakdown: dict

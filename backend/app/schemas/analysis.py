from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal
import uuid


# ── Section types ─────────────────────────────────────────────────────────

class AnalysisSection(BaseModel):
    id: str
    title: str
    type: Literal["info", "warning", "danger", "success", "neutral"]
    content: str | None = None
    items: list[str] = []
    risk_level: str | None = None
    icon: str | None = None          # Lucide icon name for frontend


class Warning(BaseModel):
    severity: Literal["critical", "high", "medium"]
    title: str
    description: str


class Recommendation(BaseModel):
    priority: Literal["critical", "high", "medium", "low"]
    action: str
    reason: str


class TimelineItem(BaseModel):
    date: str
    label: str
    type: Literal["deadline", "payment", "action", "info"]
    days_remaining: int | None = None


# ── Domain-specific data ──────────────────────────────────────────────────

class MedicalData(BaseModel):
    medicine_name: str = ""
    generic_name: str | None = None
    drug_class: str | None = None
    purpose: str = ""
    dosage: str = ""
    frequency: str = ""
    side_effects_common: list[str] = []
    side_effects_serious: list[str] = []
    warnings: list[str] = []
    alcohol_interaction: str | None = None
    food_interactions: list[str] = []
    drug_interactions: list[str] = []
    common_mistakes: list[str] = []
    emergency_warnings: list[str] = []
    disclaimer: str = "This information is for educational purposes only. Always consult a licensed healthcare professional before taking any medication."


class ScamData(BaseModel):
    probability: float = Field(0.0, ge=0.0, le=1.0)
    probability_percent: int = 0
    verdict: Literal["very_likely_scam", "suspicious", "probably_safe", "looks_legitimate"] = "probably_safe"
    verdict_label: str = "Probably Safe"
    red_flags: list[str] = []
    suspicious_urls: list[dict] = []
    manipulative_tactics: list[str] = []
    action_plan: list[str] = []
    safe_reply: str | None = None


# ── Full analysis response ────────────────────────────────────────────────

class AnalysisResponse(BaseModel):
    upload_id: str
    document_type: str
    detected_language: str
    confidence_score: float
    risk_level: str
    risk_score: int
    urgency: str
    auto_title: str
    summary: str
    sections: list[AnalysisSection]
    detected_entities: dict
    warnings: list[Warning]
    recommendations: list[Recommendation]
    timeline: list[TimelineItem]
    spending_data: dict | None = None
    medical_data: MedicalData | None = None
    scam_data: ScamData | None = None
    risk_breakdown: dict | None = None
    model_used: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Internal pipeline result (returned by pipeline.run()) ─────────────────

class PipelineResult(BaseModel):
    """What each pipeline returns after LLM analysis."""
    summary: str = ""
    sections: list[dict] = []
    warnings: list[dict] = []
    recommendations: list[dict] = []
    timeline: list[dict] = []
    spending_data: dict | None = None
    medical_data: dict | None = None
    scam_data: dict | None = None
    risk_breakdown: dict | None = None
    auto_title: str = "Document Analysis"
    model_used: str = "gemini-1.5-flash"
    token_usage: dict = {}

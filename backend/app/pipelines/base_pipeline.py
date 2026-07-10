"""Base pipeline — all domain pipelines inherit from this."""
from abc import ABC, abstractmethod
from app.services.llm_service import LLMService
from app.utils.text_utils import extract_all_entities
from app.schemas.analysis import PipelineResult


class BasePipeline(ABC):
    def __init__(self, llm: LLMService):
        self.llm = llm

    @abstractmethod
    async def run(
        self,
        text: str,
        language: str,
        image_bytes: bytes = None,
        mime_type: str = None,
    ) -> PipelineResult:
        """Run the domain-specific analysis pipeline."""
        ...

    def _calculate_risk(self, sections: list[dict]) -> tuple[int, str]:
        """Calculate risk_score (0-100) and risk_level from sections."""
        danger = sum(1 for s in sections if s.get("type") == "danger")
        warning = sum(1 for s in sections if s.get("type") == "warning")
        score = min((danger * 20) + (warning * 8), 100)
        if score >= 80:
            level = "critical"
        elif score >= 60:
            level = "high"
        elif score >= 40:
            level = "medium"
        elif score >= 20:
            level = "low"
        else:
            level = "informational"
        return score, level

    def _safe_get(self, data: dict, key: str, default=None):
        """Safely get a value from dict without KeyError."""
        return data.get(key, default) if isinstance(data, dict) else default

    def _enrich_result(self, raw: dict, text: str) -> dict:
        """Add entities extracted from raw text to the result and sanitize collections."""
        # Ensure raw is a dictionary
        if not isinstance(raw, dict):
            raw = {}

        entities = extract_all_entities(text)
        raw["detected_entities"] = entities
        raw.setdefault("sections", [])
        raw.setdefault("timeline", [])
        raw.setdefault("auto_title", "Document Analysis")
        raw.setdefault("summary", "")

        # Sanitize recommendations list to strictly match the expected Recommendation schema
        recs = raw.get("recommendations")
        clean_recs = []
        if isinstance(recs, list):
            for item in recs:
                if isinstance(item, str):
                    clean_recs.append({
                        "priority": "medium",
                        "action": item,
                        "reason": "Suggested action based on document analysis."
                    })
                elif isinstance(item, dict):
                    priority_val = str(item.get("priority") or "medium").lower()
                    if priority_val not in ("critical", "high", "medium", "low"):
                        priority_val = "medium"
                    clean_recs.append({
                        "priority": priority_val,
                        "action": str(item.get("action") or "Review document details"),
                        "reason": str(item.get("reason") or "Identified during analysis.")
                    })
        raw["recommendations"] = clean_recs

        # Sanitize warnings list to strictly match the expected Warning schema
        warns = raw.get("warnings")
        clean_warns = []
        if isinstance(warns, list):
            for item in warns:
                if isinstance(item, str):
                    clean_warns.append({
                        "severity": "medium",
                        "title": "Alert",
                        "description": item
                    })
                elif isinstance(item, dict):
                    severity_val = str(item.get("severity") or "medium").lower()
                    if severity_val not in ("critical", "high", "medium"):
                        severity_val = "medium"
                    clean_warns.append({
                        "severity": severity_val,
                        "title": str(item.get("title") or "Notice"),
                        "description": str(item.get("description") or "Potential issue detected.")
                    })
        raw["warnings"] = clean_warns

        # Sanitize sections list to strictly match the expected AnalysisSection schema
        sections = raw.get("sections")
        clean_sections = []
        if isinstance(sections, list):
            for idx, item in enumerate(sections):
                if isinstance(item, dict):
                    # Ensure type is one of the allowed literals
                    type_val = str(item.get("type") or "info").lower()
                    if type_val not in ("info", "warning", "danger", "success", "neutral"):
                        type_val = "info"

                    clean_sections.append({
                        "id": str(item.get("id") or f"sec_{idx}"),
                        "title": str(item.get("title") or "Details"),
                        "type": type_val,
                        "content": item.get("content") if item.get("content") is not None else "",
                        "items": [str(x) for x in item.get("items", [])] if isinstance(item.get("items"), list) else [],
                        "risk_level": item.get("risk_level"),
                        "icon": item.get("icon")
                    })
        raw["sections"] = clean_sections

        return raw

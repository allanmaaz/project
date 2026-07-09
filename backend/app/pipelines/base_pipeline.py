"""Base pipeline — all domain pipelines inherit from this."""
from abc import ABC, abstractmethod
from app.services.llm_service import LLMService
from app.utils.text_utils import extract_all_entities
from app.schemas.analysis import PipelineResult


class BasePipeline(ABC):
    def __init__(self, llm: LLMService):
        self.llm = llm

    @abstractmethod
    async def run(self, text: str, language: str) -> PipelineResult:
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
        """Add entities extracted from raw text to the result."""
        entities = extract_all_entities(text)
        raw["detected_entities"] = entities
        raw.setdefault("sections", [])
        raw.setdefault("warnings", [])
        raw.setdefault("recommendations", [])
        raw.setdefault("timeline", [])
        raw.setdefault("auto_title", "Document Analysis")
        raw.setdefault("summary", "")
        return raw

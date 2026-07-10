from app.pipelines.base_pipeline import BasePipeline
from app.prompts.system_prompts import get_legal_prompt
from app.schemas.analysis import PipelineResult


class LegalPipeline(BasePipeline):
    async def run(self, text: str, language: str, image_bytes: bytes = None, mime_type: str = None) -> PipelineResult:
        prompt = get_legal_prompt(language)
        raw, token_usage = await self.llm.analyze(prompt, text, language)
        raw = self._enrich_result(raw, text)
        risk_score, risk_level = self._calculate_risk(raw["sections"])

        # Legal-specific: boost risk if verdict is bad
        verdict = raw.get("verdict", "review_with_lawyer")
        if verdict == "do_not_sign":
            risk_score = max(risk_score, 75)

        return PipelineResult(
            summary=raw.get("summary", ""),
            auto_title=raw.get("auto_title", "Legal Document"),
            sections=raw.get("sections", []),
            warnings=raw.get("warnings", []),
            recommendations=raw.get("recommendations", []),
            timeline=raw.get("timeline", []),
            risk_breakdown=raw.get("risk_breakdown"),
            model_used="gemini-1.5-flash",
            token_usage=token_usage,
        )

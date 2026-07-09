from app.pipelines.base_pipeline import BasePipeline
from app.prompts.system_prompts import get_medical_prompt
from app.schemas.analysis import PipelineResult


class MedicalPipeline(BasePipeline):
    async def run(self, text: str, language: str) -> PipelineResult:
        prompt = get_medical_prompt(language)
        raw, token_usage = await self.llm.analyze(prompt, text, language)
        raw = self._enrich_result(raw, text)
        risk_score, risk_level = self._calculate_risk(raw["sections"])
        return PipelineResult(
            summary=raw.get("summary", ""),
            auto_title=raw.get("auto_title", "Medical Document"),
            sections=raw.get("sections", []),
            warnings=raw.get("warnings", []),
            recommendations=raw.get("recommendations", []),
            timeline=raw.get("timeline", []),
            medical_data=raw.get("medical_data"),
            model_used="gemini-1.5-flash",
            token_usage=token_usage,
        )

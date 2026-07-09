from app.pipelines.base_pipeline import BasePipeline
from app.prompts.system_prompts import get_government_prompt
from app.schemas.analysis import PipelineResult


class GovernmentPipeline(BasePipeline):
    async def run(self, text: str, language: str) -> PipelineResult:
        prompt = get_government_prompt(language)
        raw, token_usage = await self.llm.analyze(prompt, text, language)
        raw = self._enrich_result(raw, text)
        return PipelineResult(
            summary=raw.get("summary", ""),
            auto_title=raw.get("auto_title", "Government Document"),
            sections=raw.get("sections", []),
            warnings=raw.get("warnings", []),
            recommendations=raw.get("recommendations", []),
            timeline=raw.get("timeline", []),
            model_used="gemini-1.5-flash",
            token_usage=token_usage,
        )

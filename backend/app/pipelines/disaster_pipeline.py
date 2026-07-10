from app.pipelines.base_pipeline import BasePipeline
from app.prompts.system_prompts import get_disaster_prompt
from app.schemas.analysis import PipelineResult


class DisasterPipeline(BasePipeline):
    async def run(self, text: str, language: str) -> PipelineResult:
        prompt = get_disaster_prompt(language)
        raw, token_usage = await self.llm.analyze(prompt, text, language)
        raw = self._enrich_result(raw, text)
        return PipelineResult(
            summary=raw.get("summary", ""),
            auto_title=raw.get("auto_title", "Disaster Rescue Plan"),
            sections=raw.get("sections", []),
            warnings=raw.get("warnings", []),
            recommendations=raw.get("recommendations", []),
            timeline=raw.get("timeline", []),
            disaster_data=raw.get("disaster_data"),
            model_used="gemini-2.5-flash",
            token_usage=token_usage,
        )

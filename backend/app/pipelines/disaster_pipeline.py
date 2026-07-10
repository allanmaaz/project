from app.pipelines.base_pipeline import BasePipeline
from app.prompts.system_prompts import get_disaster_prompt
from app.schemas.analysis import PipelineResult


class DisasterPipeline(BasePipeline):
    async def run(
        self,
        text: str,
        language: str,
        image_bytes: bytes = None,
        mime_type: str = None,
    ) -> PipelineResult:
        prompt = get_disaster_prompt(language)
        # Pass image bytes so Gemini can visually analyze the flood/disaster photo
        raw, token_usage = await self.llm.analyze(
            prompt, text, language,
            image_bytes=image_bytes,
            mime_type=mime_type,
        )
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

from app.pipelines.base_pipeline import BasePipeline
from app.prompts.system_prompts import get_screenshot_prompt
from app.schemas.analysis import PipelineResult


class ScreenshotPipeline(BasePipeline):
    async def run(self, text: str, language: str, image_bytes: bytes = None, mime_type: str = None) -> PipelineResult:
        prompt = get_screenshot_prompt(language)
        raw, token_usage = await self.llm.analyze(prompt, text, language)
        raw = self._enrich_result(raw, text)
        return PipelineResult(
            summary=raw.get("summary", ""),
            auto_title=raw.get("auto_title", "Screenshot Analysis"),
            sections=raw.get("sections", []),
            warnings=raw.get("warnings", []),
            recommendations=raw.get("recommendations", []),
            timeline=[],
            model_used="gemini-1.5-flash",
            token_usage=token_usage,
        )

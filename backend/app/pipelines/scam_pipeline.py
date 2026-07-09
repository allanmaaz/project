from app.pipelines.base_pipeline import BasePipeline
from app.prompts.system_prompts import get_scam_prompt
from app.schemas.analysis import PipelineResult


class ScamPipeline(BasePipeline):
    async def run(self, text: str, language: str) -> PipelineResult:
        prompt = get_scam_prompt(language)
        raw, token_usage = await self.llm.analyze(prompt, text, language)
        raw = self._enrich_result(raw, text)

        # Compute risk score from scam probability
        scam_data = raw.get("scam_data", {}) or {}
        probability = float(scam_data.get("probability", 0.5))
        risk_score = int(probability * 100)
        scam_data["probability_percent"] = risk_score

        # Map verdict to label
        verdict_map = {
            "very_likely_scam": "Very Likely a Scam",
            "suspicious": "Suspicious — Be Careful",
            "probably_safe": "Probably Safe",
            "looks_legitimate": "Looks Legitimate",
        }
        verdict = scam_data.get("verdict", "suspicious")
        scam_data["verdict_label"] = verdict_map.get(verdict, "Unknown")

        return PipelineResult(
            summary=raw.get("summary", ""),
            auto_title=raw.get("auto_title", "Message Analysis"),
            sections=raw.get("sections", []),
            warnings=raw.get("warnings", []),
            recommendations=raw.get("recommendations", []),
            timeline=[],
            scam_data=scam_data,
            model_used="gemini-1.5-flash",
            token_usage=token_usage,
        )

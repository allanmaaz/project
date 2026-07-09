"""
Analysis Service — orchestrates the full document analysis pipeline.
Called by FastAPI BackgroundTasks after file upload.

Flow:
  upload file → store in Supabase → trigger background task → 
  OCR → classify → run pipeline → save result → update upload status
"""
import uuid
import io
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from supabase import create_client, Client

from app.config import settings
from app.models.upload import Upload
from app.models.analysis import AnalysisResult
from app.models.user import User
from app.services.ocr_service import OCRService
from app.services.classification_service import ClassificationService
from app.services.llm_service import LLMService, get_llm_service
from app.pipelines.medical_pipeline import MedicalPipeline
from app.pipelines.legal_pipeline import LegalPipeline
from app.pipelines.bill_pipeline import BillPipeline
from app.pipelines.scam_pipeline import ScamPipeline
from app.pipelines.government_pipeline import GovernmentPipeline
from app.pipelines.receipt_pipeline import ReceiptPipeline
from app.pipelines.screenshot_pipeline import ScreenshotPipeline
from app.utils.file_utils import generate_thumbnail, detect_mime_type
from app.utils.cache import analysis_cache, hash_file
from app.utils.exceptions import AnalysisFailedError


# Pipeline routing map
PIPELINE_MAP = {
    "medical": MedicalPipeline,
    "legal_contract": LegalPipeline,
    "bill_utility": BillPipeline,
    "bill_bank": BillPipeline,
    "government": GovernmentPipeline,
    "receipt_invoice": ReceiptPipeline,
    "scam_message": ScamPipeline,
    "screenshot_ui": ScreenshotPipeline,
    "unknown": ScreenshotPipeline,  # Fallback to screenshot (generic analysis)
}

# Risk level ordering for display
RISK_ORDER = {"critical": 5, "high": 4, "medium": 3, "low": 2, "informational": 1}


class AnalysisService:
    def __init__(self):
        self.classifier = ClassificationService()
        self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    async def process_upload(self, upload_id: str, db: AsyncSession) -> None:
        """
        Main background processing function.
        Called by FastAPI BackgroundTasks after file is uploaded to Supabase Storage.
        """
        # Fetch upload record
        result = await db.execute(select(Upload).where(Upload.id == upload_id))
        upload = result.scalar_one_or_none()
        if not upload:
            return

        # Fetch user for language preference
        user_result = await db.execute(select(User).where(User.id == upload.user_id))
        user = user_result.scalar_one_or_none()
        output_language = user.preferred_language if user else "en"

        try:
            # ── Step 1: Mark as processing ──────────────────────────────
            await db.execute(
                update(Upload)
                .where(Upload.id == upload_id)
                .values(status="processing", processing_started_at=datetime.utcnow())
            )
            await db.commit()

            # ── Step 2: Download file from Supabase Storage ─────────────
            file_bytes = await self._download_file(upload.storage_path)

            # ── Step 3: Check cache (same file analyzed before?) ─────────
            file_hash = hash_file(file_bytes)
            cache_key = analysis_cache.make_key(file_hash, output_language)
            cached = analysis_cache.get(cache_key)

            if cached:
                pipeline_result = cached
            else:
                # ── Step 4: OCR ──────────────────────────────────────────
                llm = get_llm_service()
                ocr_service = OCRService(gemini_model=llm.model)
                ocr_result = await ocr_service.extract(file_bytes, upload.file_type)
                extracted_text = ocr_result.text

                # ── Step 5: Classify ─────────────────────────────────────
                classification = self.classifier.classify(
                    extracted_text,
                    filename=upload.original_filename or "",
                )

                # ── Step 6: Run domain pipeline ──────────────────────────
                pipeline_class = PIPELINE_MAP.get(
                    classification.document_type, ScreenshotPipeline
                )
                pipeline = pipeline_class(llm)
                pipeline_result_obj = await pipeline.run(extracted_text, output_language)
                pipeline_result = pipeline_result_obj.model_dump()
                pipeline_result["extracted_text"] = extracted_text
                pipeline_result["document_type"] = classification.document_type
                pipeline_result["detected_language"] = classification.detected_language
                pipeline_result["confidence_score"] = classification.confidence_score
                pipeline_result["risk_level"] = classification.risk_level
                pipeline_result["urgency"] = classification.urgency

                # ── Step 7: Calculate risk score ─────────────────────────
                sections = pipeline_result.get("sections", [])
                danger = sum(1 for s in sections if s.get("type") == "danger")
                warning = sum(1 for s in sections if s.get("type") == "warning")
                risk_score = min((danger * 20) + (warning * 8), 100)
                pipeline_result["risk_score"] = risk_score

                # Override risk_level from scam_data probability if scam document
                if classification.document_type == "scam_message":
                    scam_data = pipeline_result.get("scam_data") or {}
                    prob = float(scam_data.get("probability", 0))
                    if prob >= 0.8:
                        pipeline_result["risk_level"] = "critical"
                    elif prob >= 0.6:
                        pipeline_result["risk_level"] = "high"
                    pipeline_result["risk_score"] = int(prob * 100)

                # Cache result
                analysis_cache.set(cache_key, pipeline_result)

            # ── Step 8: Generate title ───────────────────────────────────
            llm = get_llm_service()
            auto_title = await llm.generate_title(
                pipeline_result.get("extracted_text", "")[:500],
                pipeline_result.get("document_type", "unknown"),
                output_language,
            )
            pipeline_result["auto_title"] = auto_title

            # ── Step 9: Generate thumbnail ───────────────────────────────
            thumbnail_url = None
            if upload.file_type.startswith("image/"):
                try:
                    thumb_bytes = generate_thumbnail(file_bytes)
                    if thumb_bytes:
                        thumb_path = f"thumbnails/{upload.user_id}/{upload_id}.jpg"
                        self.supabase.storage.from_("thumbnails").upload(
                            thumb_path,
                            thumb_bytes,
                            {"content-type": "image/jpeg", "upsert": "true"},
                        )
                        thumbnail_url = self.supabase.storage.from_("thumbnails").get_public_url(thumb_path)
                except Exception:
                    pass  # Thumbnail is optional

            # ── Step 10: Save analysis result to DB ──────────────────────
            analysis_record = AnalysisResult(
                upload_id=upload_id,
                user_id=str(upload.user_id),
                summary=pipeline_result.get("summary", ""),
                sections=pipeline_result.get("sections", []),
                detected_entities=pipeline_result.get("detected_entities", {}),
                warnings=pipeline_result.get("warnings", []),
                recommendations=pipeline_result.get("recommendations", []),
                timeline=pipeline_result.get("timeline", []),
                spending_data=pipeline_result.get("spending_data"),
                medical_data=pipeline_result.get("medical_data"),
                scam_data=pipeline_result.get("scam_data"),
                risk_breakdown=pipeline_result.get("risk_breakdown"),
                model_used=pipeline_result.get("model_used", "gemini-1.5-flash"),
                token_usage=pipeline_result.get("token_usage", {}),
            )
            db.add(analysis_record)

            # ── Step 11: Generate suggested questions ────────────────────
            suggestions = await llm.generate_suggestions(
                pipeline_result.get("document_type", "unknown"),
                pipeline_result.get("summary", ""),
                output_language,
            )

            # ── Step 12: Update upload record ─────────────────────────────
            await db.execute(
                update(Upload)
                .where(Upload.id == upload_id)
                .values(
                    status="completed",
                    document_type=pipeline_result.get("document_type"),
                    detected_language=pipeline_result.get("detected_language", "en"),
                    confidence_score=pipeline_result.get("confidence_score", 0.8),
                    risk_level=pipeline_result.get("risk_level", "informational"),
                    risk_score=pipeline_result.get("risk_score", 0),
                    urgency=pipeline_result.get("urgency", "no_urgency"),
                    extracted_text=pipeline_result.get("extracted_text", ""),
                    auto_title=auto_title,
                    thumbnail_url=thumbnail_url,
                    suggested_questions=suggestions,
                    processing_completed_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )
            await db.commit()

        except Exception as e:
            # Mark as failed with error message
            await db.rollback()
            error_msg = str(e)[:500]
            try:
                await db.execute(
                    update(Upload)
                    .where(Upload.id == upload_id)
                    .values(
                        status="failed",
                        error_message=error_msg,
                        updated_at=datetime.utcnow(),
                    )
                )
                await db.commit()
            except Exception:
                pass

    async def _download_file(self, storage_path: str) -> bytes:
        """Download a file from Supabase Storage."""
        response = self.supabase.storage.from_("user-uploads").download(storage_path)
        if isinstance(response, bytes):
            return response
        raise AnalysisFailedError("Could not download file from storage.")


# Module-level singleton
_analysis_service: AnalysisService | None = None


def get_analysis_service() -> AnalysisService:
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service

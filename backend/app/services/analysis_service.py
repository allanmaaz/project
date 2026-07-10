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
from app.database import AsyncSessionLocal
from supabase import create_client, Client

from app.config import settings
from app.database import AsyncSessionLocal
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
from app.pipelines.disaster_pipeline import DisasterPipeline
from app.utils.file_utils import generate_thumbnail, detect_mime_type
from app.utils.cache import analysis_cache, hash_file, CACHE_VERSION
from app.utils.exceptions import AnalysisFailedError
from app.services.vision_service import get_vision_service
from app.services.video_service import get_video_service

# Supported video MIME types
VIDEO_MIME_TYPES = {
    "video/mp4", "video/webm", "video/quicktime",
    "video/avi", "video/x-msvideo", "video/mov",
}


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
    "disaster_rescue": DisasterPipeline,
    "unknown": ScreenshotPipeline,  # Fallback to screenshot (generic analysis)
}

# Risk level ordering for display
RISK_ORDER = {"critical": 5, "high": 4, "medium": 3, "low": 2, "informational": 1}


class AnalysisService:
    def __init__(self):
        self.classifier = ClassificationService()
        self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    async def process_upload(self, upload_id: str, provider: str = "gemini") -> None:
        """
        Main background processing function.
        Called by FastAPI BackgroundTasks after file is uploaded to Supabase Storage.
        Creates its own database session to avoid using a closed request-scoped session.
        """
        from app.services.llm_service import active_llm_provider
        token = active_llm_provider.set(provider)
        try:
            async with AsyncSessionLocal() as db:
                await self._process_upload_with_db(upload_id, db)
        finally:
            active_llm_provider.reset(token)

    async def _process_upload_with_db(self, upload_id: str, db: AsyncSession) -> None:
        """
        Internal method that does the actual processing with a provided DB session.
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
        llm = get_llm_service()

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

            # ── Step 3: Check cache (same file analyzed before?) ─────
            file_hash = hash_file(file_bytes)
            # CACHE_VERSION is bumped when prompts change so stale results are bypassed
            cache_key = analysis_cache.make_key(file_hash, output_language, CACHE_VERSION)
            cached = analysis_cache.get(cache_key)

            if cached:
                pipeline_result = cached
            else:
                # ── Step 4: OCR ──────────────────────────────────────────
                llm = get_llm_service()
                ocr_service = OCRService(gemini_model=llm.model)
                ocr_result = await ocr_service.extract(file_bytes, upload.file_type)
                extracted_text = ocr_result.text

                # Update database with extracted text to update progress bar step in frontend
                await db.execute(
                    update(Upload)
                    .where(Upload.id == upload_id)
                    .values(extracted_text=extracted_text, updated_at=datetime.utcnow())
                )
                await db.commit()

                # ── Step 5: Classify ─────────────────────────────────────
                classification = self.classifier.classify(
                    extracted_text,
                    filename=upload.original_filename or "",
                )

                # ── Step 5b: YOLO Vision Detection (images + videos) ─────
                is_image = upload.file_type.startswith("image/")
                is_video = upload.file_type in VIDEO_MIME_TYPES
                detections_data = None
                video_data = None

                if is_image:
                    try:
                        print(f"[Vision] Running YOLOv8n on image...")
                        vision = get_vision_service()
                        detections_data = await vision.detect(file_bytes, upload.file_type)
                        print(f"[Vision] Detected {detections_data['total_objects']} objects: {detections_data['summary']}")

                        # Generate + upload annotated image (with bounding boxes drawn)
                        if detections_data["detections"]:
                            ann_bytes = await vision.draw_annotated(
                                file_bytes,
                                detections_data["detections"],
                                detections_data["image_width"],
                                detections_data["image_height"],
                            )
                            ann_path = f"annotated/{upload.user_id}/{upload_id}.jpg"
                            try:
                                self.supabase.storage.from_("thumbnails").upload(
                                    ann_path, ann_bytes,
                                    {"content-type": "image/jpeg", "upsert": "true"},
                                )
                                ann_url = self.supabase.storage.from_("thumbnails").get_public_url(ann_path)
                                await db.execute(
                                    update(Upload).where(Upload.id == upload_id)
                                    .values(annotated_image_url=ann_url)
                                )
                                await db.commit()
                            except Exception as ann_err:
                                print(f"[Vision] Annotated upload failed: {ann_err}")

                        # Use YOLO detections to boost classification accuracy
                        summary = detections_data.get("summary", {})
                        if classification.document_type in ("unknown", "screenshot_ui"):
                            person_count = summary.get("person", 0)
                            water_keywords = any(k in str(summary).lower() for k in ["boat", "water"])
                            vehicle_count = sum(summary.get(v, 0) for v in ["car", "truck", "bus", "motorcycle"])
                            if person_count >= 2 or water_keywords:
                                classification.document_type = "disaster_rescue"
                                print(f"[Vision] YOLO override: disaster_rescue (persons={person_count})")

                    except Exception as ve:
                        print(f"[Vision] Detection failed (non-fatal): {ve}")

                elif is_video:
                    try:
                        print(f"[Vision] Running video frame analysis...")
                        vision = get_vision_service()
                        video_svc = get_video_service()
                        video_data = await video_svc.process_video(file_bytes, vision)
                        print(f"[Vision] Video: {video_data.get('sampled_frames')} frames, peaks: {video_data.get('aggregate_summary')}")
                        classification.document_type = "disaster_rescue"  # videos default to scene analysis
                        
                        # Extract thumbnail grid bytes to upload separately (bytes are not JSON-serializable)
                        grid_bytes = video_data.pop("thumbnail_grid", None)
                        if grid_bytes:
                            grid_path = f"thumbnails/{upload.user_id}/{upload_id}_grid.jpg"
                            try:
                                self.supabase.storage.from_("thumbnails").upload(
                                    grid_path, grid_bytes,
                                    {"content-type": "image/jpeg", "upsert": "true"},
                                )
                                grid_url = self.supabase.storage.from_("thumbnails").get_public_url(grid_path)
                                video_data["thumbnail_grid_url"] = grid_url
                                print(f"[Vision] Video thumbnail grid uploaded to: {grid_url}")
                            except Exception as grid_err:
                                print(f"[Vision] Video grid upload failed: {grid_err}")

                        await db.execute(
                            update(Upload).where(Upload.id == upload_id)
                            .values(video_frame_count=video_data.get("frame_count", 0))
                        )
                        await db.commit()
                    except Exception as ve:
                        print(f"[Vision] Video analysis failed (non-fatal): {ve}")

                # If still unknown image → use Gemini visual classification
                if classification.document_type == "unknown" and is_image and len(extracted_text.strip()) < 30:
                    try:
                        print(f"[Analysis] Running Gemini visual classification fallback")
                        visual_type = await llm.classify_visually(file_bytes, upload.file_type)
                        if visual_type != "unknown":
                            print(f"[Analysis] Gemini visual: {visual_type}")
                            classification.document_type = visual_type
                    except Exception as ve:
                        print(f"[Analysis] Gemini visual classification failed: {ve}")

                # Store detections in DB (for chat context + frontend viewer)
                det_to_store = detections_data if detections_data else []
                vd_to_store = video_data if video_data else None
                await db.execute(
                    update(Upload).where(Upload.id == upload_id).values(
                        detections=det_to_store,
                        video_detections=vd_to_store,
                    )
                )
                await db.commit()

                # ── Step 6: Run domain pipeline ──────────────────────────
                pipeline_class = PIPELINE_MAP.get(
                    classification.document_type, ScreenshotPipeline
                )
                pipeline = pipeline_class(llm)
                # Pass image bytes for image uploads so pipeline can do visual analysis
                img_bytes = file_bytes if is_image else None
                img_mime = upload.file_type if is_image else None
                pipeline_result_obj = await pipeline.run(
                    extracted_text, output_language,
                    image_bytes=img_bytes, mime_type=img_mime
                )
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

            # ── Step 8: Generate title (only if not already generated by pipeline) ──
            auto_title = pipeline_result.get("auto_title")
            if not auto_title:
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
                disaster_data=pipeline_result.get("disaster_data"),
                risk_breakdown=pipeline_result.get("risk_breakdown"),
                model_used=pipeline_result.get("model_used", "gemini-2.5-flash"),
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
            # Mark as failed with error message using a fresh session
            error_msg = str(e)[:500]
            async with AsyncSessionLocal() as error_db:
                try:
                    await error_db.execute(
                        update(Upload)
                        .where(Upload.id == upload_id)
                        .values(
                            status="failed",
                            error_message=error_msg,
                            updated_at=datetime.utcnow(),
                        )
                    )
                    await error_db.commit()
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

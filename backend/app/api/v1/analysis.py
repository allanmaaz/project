from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import uuid
import secrets
from datetime import datetime, timedelta

from app.database import get_db
from app.middleware.auth import CurrentUser
from app.models.upload import Upload, SharedAnalysis
from app.models.analysis import AnalysisResult
from app.models.user import User
from app.schemas.analysis import AnalysisResponse
from app.services.pdf_service import get_pdf_service
from app.utils.exceptions import raise_http, NotFoundError, ForbiddenError

router = APIRouter()

@router.get("/{upload_id}", response_model=AnalysisResponse)
async def get_analysis(
    upload_id: str,
    current_user: User = CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve the full parsed structured AI analysis for a completed document."""
    upload_uuid = uuid.UUID(upload_id)
    
    # Verify ownership of upload
    upload_res = await db.execute(select(Upload).where(Upload.id == upload_uuid))
    upload = upload_res.scalar_one_or_none()
    if not upload:
        raise_http(NotFoundError("Document"), 404)
    if upload.user_id != current_user.id:
        raise_http(ForbiddenError(), 403)

    if upload.status != "completed":
        raise_http(NotFoundError("Analysis result is not ready or has failed."), 400)

    # Fetch analysis result
    analysis_res = await db.execute(select(AnalysisResult).where(AnalysisResult.upload_id == upload_uuid))
    analysis = analysis_res.scalar_one_or_none()
    if not analysis:
        raise_http(NotFoundError("AnalysisResult"), 404)

    # Convert to response schema
    return AnalysisResponse(
        upload_id=str(upload.id),
        document_type=upload.document_type,
        detected_language=upload.detected_language,
        confidence_score=upload.confidence_score or 0.0,
        risk_level=upload.risk_level or "informational",
        risk_score=upload.risk_score,
        urgency=upload.urgency or "no_urgency",
        auto_title=upload.auto_title or "Untitled",
        summary=analysis.summary,
        sections=analysis.sections,
        detected_entities=analysis.detected_entities,
        warnings=analysis.warnings,
        recommendations=analysis.recommendations,
        timeline=analysis.timeline,
        spending_data=analysis.spending_data,
        medical_data=analysis.medical_data,
        scam_data=analysis.scam_data,
        risk_breakdown=analysis.risk_breakdown,
        model_used=analysis.model_used,
        created_at=analysis.created_at,
    )


@router.post("/{upload_id}/export")
async def export_analysis_pdf(
    upload_id: str,
    current_user: User = CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Export the structured analysis as an Apple-inspired clean PDF."""
    upload_uuid = uuid.UUID(upload_id)
    
    upload_res = await db.execute(select(Upload).where(Upload.id == upload_uuid))
    upload = upload_res.scalar_one_or_none()
    if not upload or upload.user_id != current_user.id:
        raise_http(NotFoundError("Document"), 404)

    analysis_res = await db.execute(select(AnalysisResult).where(AnalysisResult.upload_id == upload_uuid))
    analysis = analysis_res.scalar_one_or_none()
    if not analysis:
        raise_http(NotFoundError("Analysis"), 404)

    pdf_bytes = get_pdf_service().generate_analysis_pdf(upload, analysis)

    filename = f"ClarifyAI_{upload.auto_title.replace(' ', '_')}.pdf" if upload.auto_title else "Analysis.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "no-cache"
        }
    )


@router.post("/{upload_id}/share")
async def generate_share_link(
    upload_id: str,
    days_to_expire: int = 7,
    current_user: User = CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Generate a share link that expires after a defined window."""
    upload_uuid = uuid.UUID(upload_id)
    
    upload_res = await db.execute(select(Upload).where(Upload.id == upload_uuid))
    upload = upload_res.scalar_one_or_none()
    if not upload or upload.user_id != current_user.id:
        raise_http(NotFoundError("Document"), 404)

    share_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=days_to_expire)

    shared = SharedAnalysis(
        upload_id=upload.id,
        user_id=current_user.id,
        share_token=share_token,
        expires_at=expires_at
    )
    db.add(shared)
    await db.commit()

    return {
        "share_token": share_token,
        "expires_at": expires_at.isoformat(),
        "share_url": f"/shared/{share_token}"
    }


@router.get("/shared/{token}", response_model=AnalysisResponse)
async def get_shared_analysis(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve shared analysis result by token, bypasses direct user authentication."""
    shared_res = await db.execute(
        select(SharedAnalysis).where(SharedAnalysis.share_token == token)
    )
    shared = shared_res.scalar_one_or_none()
    
    if not shared or shared.expires_at < datetime.utcnow():
        raise_http(NotFoundError("Shared link expired or invalid."), 404)

    # Increment view count
    await db.execute(
        update(SharedAnalysis)
        .where(SharedAnalysis.id == shared.id)
        .values(view_count=shared.view_count + 1)
    )

    upload_res = await db.execute(select(Upload).where(Upload.id == shared.upload_id))
    upload = upload_res.scalar_one_or_none()
    
    analysis_res = await db.execute(select(AnalysisResult).where(AnalysisResult.upload_id == shared.upload_id))
    analysis = analysis_res.scalar_one_or_none()

    return AnalysisResponse(
        upload_id=str(upload.id),
        document_type=upload.document_type,
        detected_language=upload.detected_language,
        confidence_score=upload.confidence_score or 0.0,
        risk_level=upload.risk_level or "informational",
        risk_score=upload.risk_score,
        urgency=upload.urgency or "no_urgency",
        auto_title=upload.auto_title or "Untitled",
        summary=analysis.summary,
        sections=analysis.sections,
        detected_entities=analysis.detected_entities,
        warnings=analysis.warnings,
        recommendations=analysis.recommendations,
        timeline=analysis.timeline,
        spending_data=analysis.spending_data,
        medical_data=analysis.medical_data,
        scam_data=analysis.scam_data,
        risk_breakdown=analysis.risk_breakdown,
        model_used=analysis.model_used,
        created_at=analysis.created_at,
    )

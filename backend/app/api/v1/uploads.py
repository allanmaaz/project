from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from supabase import create_client, Client
import uuid
import math
from datetime import datetime

from app.config import settings
from app.database import get_db
from app.middleware.auth import CurrentUser
from app.middleware.rate_limit import check_upload_rate, check_monthly_limit
from app.models.upload import Upload
from app.models.user import User
from app.schemas.upload import UploadCreateResponse, UploadStatusResponse, UploadListResponse, UploadListItem
from app.services.analysis_service import get_analysis_service
from app.utils.file_utils import detect_mime_type, validate_file
from app.utils.exceptions import raise_http, NotFoundError, ForbiddenError, ClarifyBaseError

router = APIRouter()
supabase_client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

@router.post("", response_model=UploadCreateResponse)
async def create_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Directly upload a document to Supabase storage, insert a DB entry,
    and schedule a background worker task to process the document.
    """
    try:
        # Check limits
        await check_upload_rate(current_user)
        check_monthly_limit(current_user)
    except ClarifyBaseError as e:
        raise_http(e, 429)

    # Read bytes for validation
    file_bytes = await file.read()
    
    try:
        mime_type = detect_mime_type(file_bytes)
        validate_file(file_bytes, mime_type, settings.max_file_bytes)
    except ClarifyBaseError as e:
        raise_http(e, 400)

    # Scaffolding directory path inside Supabase user-uploads bucket
    upload_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "dat"
    storage_path = f"{current_user.id}/{upload_id}.{ext}"

    # Upload to Supabase Storage
    try:
        supabase_client.storage.from_("user-uploads").upload(
            storage_path,
            file_bytes,
            {"content-type": mime_type}
        )
    except Exception as e:
        raise_http(ClarifyBaseError(f"Failed to save file to cloud storage: {str(e)}"), 500)

    # Create the pending upload record in DB
    db_upload = Upload(
        id=uuid.UUID(upload_id),
        user_id=current_user.id,
        original_filename=file.filename,
        storage_path=storage_path,
        file_type=mime_type,
        file_size_bytes=len(file_bytes),
        status="pending",
    )
    db.add(db_upload)

    # Update monthly stats
    current_user.uploads_this_month += 1
    current_user.total_uploads += 1
    
    await db.commit()

    # Dispatch to asynchronous processing pipeline
    from app.services.llm_service import active_llm_provider
    provider = active_llm_provider.get()
    analysis_srv = get_analysis_service()
    background_tasks.add_task(analysis_srv.process_upload, upload_id, provider)

    return UploadCreateResponse(upload_id=upload_id)


@router.get("/{upload_id}/status", response_model=UploadStatusResponse)
async def get_upload_status(
    upload_id: str,
    current_user: User = CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Poll status of background analysis task."""
    result = await db.execute(select(Upload).where(Upload.id == uuid.UUID(upload_id)))
    upload = result.scalar_one_or_none()
    
    if not upload:
        raise_http(NotFoundError("Upload"), 404)
        
    if upload.user_id != current_user.id:
        raise_http(ForbiddenError(), 403)

    progress = 0
    step = "pending"
    if upload.status == "processing":
        step = "ocr"
        progress = 30
        if upload.extracted_text:
            step = "analysis"
            progress = 75
    elif upload.status == "completed":
        step = "done"
        progress = 100
    elif upload.status == "failed":
        step = "failed"
        progress = 0

    return UploadStatusResponse(
        upload_id=str(upload.id),
        status=upload.status,
        step=step,
        progress_percent=progress,
        error=upload.error_message,
    )


@router.get("", response_model=UploadListResponse)
async def list_uploads(
    page: int = Query(1, ge=1),
    per_page: int = Query(12, ge=1, le=100),
    q: str | None = None,
    doc_type: str | None = None,
    risk_level: str | None = None,
    current_user: User = CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve history of uploaded documents with full-text search and filtering."""
    query = select(Upload).where(Upload.user_id == current_user.id)

    # Full text search or keyword match
    conditions = []
    if q:
        conditions.append(
            and_(
                Upload.original_filename.ilike(f"%{q}%") |
                Upload.auto_title.ilike(f"%{q}%") |
                Upload.extracted_text.ilike(f"%{q}%")
            )
        )
    if doc_type:
        conditions.append(Upload.document_type == doc_type)
    if risk_level:
        conditions.append(Upload.risk_level == risk_level)

    if conditions:
        query = query.where(*conditions)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_count_res = await db.execute(count_query)
    total_count = total_count_res.scalar() or 0

    # Paginate and sort (newest first)
    query = query.order_by(desc(Upload.created_at)).offset((page - 1) * per_page).limit(per_page)
    results = await db.execute(query)
    items = results.scalars().all()

    return UploadListResponse(
        items=[UploadListItem.model_validate(item) for item in items],
        total=total_count,
        page=page,
        per_page=per_page
    )


@router.delete("/{upload_id}")
async def delete_upload(
    upload_id: str,
    current_user: User = CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Delete a document, cascade DB deletions, and purge from storage."""
    result = await db.execute(select(Upload).where(Upload.id == uuid.UUID(upload_id)))
    upload = result.scalar_one_or_none()
    
    if not upload:
        raise_http(NotFoundError("Upload"), 404)
        
    if upload.user_id != current_user.id:
        raise_http(ForbiddenError(), 403)

    # Remove storage files (raw file + thumbnail)
    try:
        supabase_client.storage.from_("user-uploads").remove([upload.storage_path])
        if upload.thumbnail_url:
            thumb_path = f"thumbnails/{current_user.id}/{upload.id}.jpg"
            supabase_client.storage.from_("thumbnails").remove([thumb_path])
    except Exception:
        pass # Graceful on storage delete issues

    await db.delete(upload)
    await db.commit()

    return {"status": "success", "message": "Document deleted successfully."}


@router.get("/{upload_id}/detections")
async def get_detections(
    upload_id: str,
    current_user: User = CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Return YOLOv8n detection data for an upload.
    - detections: bounding boxes with label, confidence, bbox coords, color
    - summary: {'person': 3, 'car': 2, ...}
    - annotated_image_url: image with boxes drawn
    - video_detections: per-frame analysis for video uploads
    """
    result = await db.execute(select(Upload).where(Upload.id == uuid.UUID(upload_id)))
    upload = result.scalar_one_or_none()

    if not upload:
        raise_http(NotFoundError("Upload"), 404)
    if upload.user_id != current_user.id:
        raise_http(ForbiddenError(), 403)

    return {
        "upload_id": str(upload.id),
        "detections": upload.detections or [],
        "video_detections": upload.video_detections,
        "annotated_image_url": upload.annotated_image_url,
        "video_frame_count": upload.video_frame_count,
        "document_type": upload.document_type,
        "has_detections": bool(upload.detections),
        "has_video": bool(upload.video_detections),
    }


from fastapi.responses import Response

@router.get("/{upload_id}/raw")
async def get_raw_file(
    upload_id: str,
    current_user: User = CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Stream the raw file from Supabase Storage."""
    result = await db.execute(select(Upload).where(Upload.id == uuid.UUID(upload_id)))
    upload = result.scalar_one_or_none()

    if not upload:
        raise_http(NotFoundError("Upload"), 404)
    if upload.user_id != current_user.id:
        raise_http(ForbiddenError(), 403)

    try:
        # download returns bytes
        file_bytes = supabase_client.storage.from_("user-uploads").download(upload.storage_path)
        return Response(content=file_bytes, media_type=upload.file_type)
    except Exception as e:
        raise_http(ClarifyBaseError(f"Failed to retrieve file from cloud storage: {str(e)}"), 500)

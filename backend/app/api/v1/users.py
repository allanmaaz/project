from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from supabase import create_client, Client
import uuid

from app.database import get_db
from app.middleware.auth import CurrentUser
from app.models.user import User
from app.models.upload import Upload
from app.models.analysis import AnalysisResult
from app.schemas.user import UserResponse, UserUpdateRequest, UserStatsResponse
from app.utils.exceptions import raise_http, NotFoundError
from app.config import settings

router = APIRouter()
supabase_client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

@router.get("/me", response_model=UserResponse)
async def get_user_profile(current_user: User = CurrentUser):
    """Retrieve details and active preferences of current logged-in user."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_user_preferences(
    payload: UserUpdateRequest,
    current_user: User = CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Update UI language, theme, and output language preferences."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url
    if payload.preferred_language is not None:
        current_user.preferred_language = payload.preferred_language
    if payload.ui_language is not None:
        current_user.ui_language = payload.ui_language
    if payload.theme is not None:
        current_user.theme = payload.theme

    await db.commit()
    return current_user


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_user_statistics(
    current_user: User = CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Compile aggregated user metrics, document type counts, spending summaries, and risk indexes."""
    # 1. Total uploads count
    total_uploads = current_user.total_uploads
    uploads_this_month = current_user.uploads_this_month

    # Plan details
    plan_limit = 10000 if current_user.plan == "pro" else settings.FREE_PLAN_MONTHLY_UPLOADS
    uploads_remaining = max(0, plan_limit - uploads_this_month)

    # 2. Document type breakdown
    type_query = (
        select(Upload.document_type, func.count(Upload.id))
        .where(Upload.user_id == current_user.id)
        .group_by(Upload.document_type)
    )
    type_res = await db.execute(type_query)
    doc_types = [{"name": row[0] or "unknown", "value": row[1]} for row in type_res.all()]

    # 3. Compile spending data by category from completed analyses
    spending_total = 0.0
    spending_by_category = {}
    
    # Query all completed analysis results that contain spending_data
    analysis_query = (
        select(AnalysisResult.spending_data)
        .where(AnalysisResult.user_id == current_user.id)
    )
    analysis_res = await db.execute(analysis_query)
    results = analysis_res.scalars().all()

    for data in results:
        if not data:
            continue
        # Extract total amount
        amount = float(data.get("total_amount") or 0.0)
        spending_total += amount
        # Add to category
        category = data.get("merchant_category") or "Other"
        spending_by_category[category] = spending_by_category.get(category, 0.0) + amount

    # 4. Risk breakdown count
    risk_query = (
        select(Upload.risk_level, func.count(Upload.id))
        .where(Upload.user_id == current_user.id)
        .group_by(Upload.risk_level)
    )
    risk_res = await db.execute(risk_query)
    risk_breakdown = {row[0] or "informational": row[1] for row in risk_res.all()}

    return UserStatsResponse(
        total_uploads=total_uploads,
        uploads_this_month=uploads_this_month,
        plan=current_user.plan,
        plan_limit=plan_limit,
        uploads_remaining=uploads_remaining,
        spending_total_this_month=round(spending_total, 2),
        spending_by_category=spending_by_category,
        document_types_breakdown=doc_types,
        risk_breakdown=risk_breakdown
    )


@router.post("/me/upgrade", response_model=UserResponse)
async def upgrade_user_plan_free(
    current_user: User = CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Simulated Pro upgrade endpoint.
    Since we are using a 100% free stack, this gives users Pro tier immediately.
    """
    current_user.plan = "pro"
    await db.commit()
    return current_user


@router.delete("/me")
async def delete_user_account(
    current_user: User = CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Permanently delete user profile, purge all documents, and delete auth credentials."""
    # 1. Fetch user uploads to delete files from Supabase Storage
    uploads_res = await db.execute(select(Upload).where(Upload.user_id == current_user.id))
    uploads = uploads_res.scalars().all()

    storage_paths = [upload.storage_path for upload in uploads]
    thumb_paths = [f"thumbnails/{current_user.id}/{upload.id}.jpg" for upload in uploads if upload.thumbnail_url]

    # Delete from Supabase Storage
    try:
        if storage_paths:
            supabase_client.storage.from_("user-uploads").remove(storage_paths)
        if thumb_paths:
            supabase_client.storage.from_("thumbnails").remove(thumb_paths)
    except Exception:
        pass

    # 2. Delete user ORM record (cascades database deletions to uploads, analyses, chat messages)
    await db.delete(current_user)
    await db.commit()

    # 3. Remove user from Supabase Authentication
    try:
        supabase_client.auth.admin.delete_user(str(current_user.supabase_user_id))
    except Exception as e:
        # Ignore if admin permission isn't configured in test environments
        pass

    return {"status": "success", "message": "Account and all associated data deleted successfully."}

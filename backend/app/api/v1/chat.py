from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import json
from typing import AsyncGenerator

from app.database import get_db
from app.middleware.auth import CurrentUser
from app.middleware.rate_limit import check_chat_rate
from app.models.upload import Upload
from app.models.chat import ChatMessage
from app.models.analysis import AnalysisResult
from app.models.user import User
from app.schemas.chat import ChatHistoryResponse, ChatMessageResponse, SuggestionsResponse
from app.services.llm_service import get_llm_service
from app.utils.exceptions import raise_http, NotFoundError, ForbiddenError, ClarifyBaseError

router = APIRouter()

@router.get("/{upload_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    upload_id: str,
    current_user: User = CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve persistent conversation history associated with a document upload."""
    upload_uuid = uuid.UUID(upload_id)
    upload_res = await db.execute(select(Upload).where(Upload.id == upload_uuid))
    upload = upload_res.scalar_one_or_none()

    if not upload or upload.user_id != current_user.id:
        raise_http(NotFoundError("Document"), 404)

    chat_res = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.upload_id == upload_uuid)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = chat_res.scalars().all()

    return ChatHistoryResponse(
        messages=[ChatMessageResponse.model_validate(msg) for msg in messages]
    )


@router.get("/{upload_id}/suggestions", response_model=SuggestionsResponse)
async def get_chat_suggestions(
    upload_id: str,
    current_user: User = CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve pre-generated contextual questions to help start a Q&A conversation."""
    upload_uuid = uuid.UUID(upload_id)
    upload_res = await db.execute(select(Upload).where(Upload.id == upload_uuid))
    upload = upload_res.scalar_one_or_none()

    if not upload or upload.user_id != current_user.id:
        raise_http(NotFoundError("Document"), 404)

    return SuggestionsResponse(suggestions=upload.suggested_questions or [])


@router.get("/{upload_id}/stream")
async def stream_chat_response(
    upload_id: str,
    message: str = Query(..., min_length=1),
    current_user: User = CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Stream real-time Gemini answers via Server-Sent Events (SSE).
    Includes history context + RLS authorization checks.
    """
    try:
        check_chat_rate(current_user)
    except ClarifyBaseError as e:
        raise_http(e, 429)

    upload_uuid = uuid.UUID(upload_id)
    upload_res = await db.execute(select(Upload).where(Upload.id == upload_uuid))
    upload = upload_res.scalar_one_or_none()

    if not upload or upload.user_id != current_user.id:
        raise_http(NotFoundError("Document"), 404)

    analysis_res = await db.execute(select(AnalysisResult).where(AnalysisResult.upload_id == upload_uuid))
    analysis = analysis_res.scalar_one_or_none()
    if not analysis:
        raise_http(NotFoundError("Analysis results are not ready for this document."), 400)

    # 1. Retrieve message history (convert to dict format for LLM service)
    chat_res = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.upload_id == upload_uuid)
        .order_by(ChatMessage.created_at.asc())
    )
    historical_messages = chat_res.scalars().all()

    chat_history = []
    for msg in historical_messages:
        chat_history.append({"role": msg.role, "content": msg.content})

    # Append new user message to chat history representation
    chat_history.append({"role": "user", "content": message})

    # 2. Persist the user's message to database
    db_user_msg = ChatMessage(
        upload_id=upload_uuid,
        user_id=current_user.id,
        role="user",
        content=message
    )
    db.add(db_user_msg)
    await db.commit()

    async def sse_event_generator() -> AsyncGenerator[str, None]:
        llm = get_llm_service()
        response_accumulator = []

        try:
            # Yield initial token response indicator
            yield f"data: {json.dumps({'event': 'start'})}\n\n"

            # Call LLM streaming pipeline
            stream = llm.stream_chat(
                history=chat_history,
                doc_context=upload.extracted_text or "",
                doc_type=upload.document_type or "unknown",
                analysis_summary=analysis.summary,
                output_language=current_user.preferred_language,
            )

            async for chunk in stream:
                response_accumulator.append(chunk)
                yield f"data: {json.dumps({'token': chunk})}\n\n"

            full_response = "".join(response_accumulator)

            # Persist assistant's message in DB
            # We open a clean session internally as SSE keeps the original route thread open
            # so we commit directly to DB session in background
            db_ai_msg = ChatMessage(
                upload_id=upload_uuid,
                user_id=current_user.id,
                role="assistant",
                content=full_response
            )
            db.add(db_ai_msg)
            await db.commit()

            yield f"data: {json.dumps({'event': 'done', 'response': full_response})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

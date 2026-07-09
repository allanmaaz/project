from fastapi import APIRouter
from app.api.v1 import uploads, analysis, chat, users, health

v1_router = APIRouter()

v1_router.include_router(health.router, tags=["Health"])
v1_router.include_router(uploads.router, prefix="/uploads", tags=["Uploads"])
v1_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
v1_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
v1_router.include_router(users.router, prefix="/users", tags=["Users"])

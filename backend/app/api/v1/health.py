from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
import time

router = APIRouter()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint to monitor DB availability and system status."""
    start_time = time.time()
    db_status = "healthy"
    try:
        # Quick query validation to test DB connection
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "latency_ms": round((time.time() - start_time) * 1000, 2),
        "timestamp": time.time(),
    }

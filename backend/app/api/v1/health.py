from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
import time
try:
    import psutil
except ImportError:
    psutil = None
import os

router = APIRouter()

# Track startup time for liveness
_start_time = time.time()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint - liveness probe."""
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - _start_time, 2),
    }

@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check endpoint - includes DB, memory, disk checks.
    Returns 503 if not ready to serve traffic.
    """
    checks = {}
    overall_ready = True

    # Database check
    db_start = time.time()
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {
            "status": "healthy",
            "latency_ms": round((time.time() - db_start) * 1000, 2)
        }
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        overall_ready = False

    # Memory check (warn if > 85%)
    if psutil:
        mem = psutil.virtual_memory()
        checks["memory"] = {
            "status": "healthy" if mem.percent < 85 else "warning",
            "usage_percent": mem.percent,
            "available_mb": round(mem.available / 1024 / 1024, 2)
        }
        if mem.percent >= 95:
            overall_ready = False
    else:
        checks["memory"] = {
            "status": "healthy",
            "usage_percent": 0.0,
            "available_mb": 0.0,
            "note": "psutil not available"
        }

    # Disk check (warn if > 85%)
    if psutil:
        disk = psutil.disk_usage("/")
        checks["disk"] = {
            "status": "healthy" if disk.percent < 85 else "warning",
            "usage_percent": disk.percent,
            "free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
        }
        if disk.percent >= 95:
            overall_ready = False
    else:
        try:
            st = os.statvfs('/')
            free = (st.f_bavail * st.f_frsize)
            total = (st.f_blocks * st.f_frsize)
            used = total - free
            percent = (used / total) * 100
            checks["disk"] = {
                "status": "healthy" if percent < 85 else "warning",
                "usage_percent": round(percent, 2),
                "free_gb": round(free / 1024 / 1024 / 1024, 2)
            }
        except Exception:
            checks["disk"] = {
                "status": "healthy",
                "usage_percent": 0.0,
                "free_gb": 0.0,
                "note": "disk check not available"
            }

    # Redis check (optional - don't fail readiness if Redis is down)
    try:
        from app.services.rate_limiter import RedisRateLimiter
        limiter = RedisRateLimiter()
        await limiter._get_client()
        await limiter.close()
        checks["redis"] = {"status": "healthy"}
    except Exception:
        checks["redis"] = {"status": "unhealthy", "note": "falling back to in-memory"}

    if not overall_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "checks": checks}
        )

    return {"status": "ready", "checks": checks}

@router.get("/live")
async def liveness_check():
    """Liveness probe - just checks if process is alive."""
    return {"status": "alive", "uptime_seconds": round(time.time() - _start_time, 2)}

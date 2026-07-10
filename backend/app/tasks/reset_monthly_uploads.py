"""
Monthly upload counter reset task.
Run via cron (e.g., Supabase pg_cron, Cloud Run Jobs, or system cron).
"""
import asyncio
from sqlalchemy import update
from app.database import AsyncSessionLocal
from app.models.user import User


async def reset_monthly_uploads() -> int:
    """
    Reset uploads_this_month counter for all users.
    Returns number of affected rows.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            update(User).values(uploads_this_month=0)
        )
        await db.commit()
        return result.rowcount


async def main():
    """Entry point for scheduled execution."""
    try:
        count = await reset_monthly_uploads()
        print(f"Successfully reset monthly uploads for {count} users")
    except Exception as e:
        print(f"ERROR: Failed to reset monthly uploads: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
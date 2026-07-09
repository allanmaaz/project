"""
JWT authentication middleware using Supabase JWT tokens.
Validates the Bearer token, extracts user, injects into request.state.
"""
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.database import get_db
from app.models.user import User


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate Supabase JWT.
    Returns the User ORM object or raises 401.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Authentication required."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},  # Supabase uses 'authenticated' as audience
        )
        supabase_user_id: str = payload.get("sub")
        if not supabase_user_id:
            raise JWTError("Missing sub claim")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid or expired token."},
        )

    # Look up user in our DB
    result = await db.execute(
        select(User).where(User.supabase_user_id == supabase_user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        # Auto-create user record if it doesn't exist yet
        # (Supabase trigger should handle this, but this is a safety net)
        email = payload.get("email", "")
        user = User(
            supabase_user_id=supabase_user_id,
            email=email,
            full_name=payload.get("user_metadata", {}).get("full_name"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


# Alias for cleaner endpoint signatures
CurrentUser = Depends(get_current_user)

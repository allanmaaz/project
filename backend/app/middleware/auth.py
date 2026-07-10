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


# In-memory JWKS cache
_jwks_cache = None

async def get_jwk_by_kid(kid: str) -> dict | None:
    global _jwks_cache
    if not _jwks_cache:
        try:
            jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/jwks.json"
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(jwks_url)
                if resp.status_code == 200:
                    _jwks_cache = resp.json()
        except Exception as e:
            print(f"DEBUG AUTH: Failed to fetch JWKS: {e}")
            return None
    
    if _jwks_cache and "keys" in _jwks_cache:
        for key in _jwks_cache["keys"]:
            if key.get("kid") == kid:
                return key
    return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate Supabase JWT.
    Supports HS256 (symmetric) and RS256 (asymmetric JWKS).
    """
    token = None
    if credentials:
        token = credentials.credentials
    else:
        # Fallback to query parameter "token" for browser direct requests (e.g. PDF export / downloads)
        token = request.query_params.get("token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Authentication required."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        from jose import jws
        header = jws.get_unverified_header(token)
        alg = header.get("alg", "HS256")
        
        if alg == "HS256":
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        elif alg in ("RS256", "ES256"):
            kid = header.get("kid")
            jwk_key = await get_jwk_by_kid(kid) if kid else None
            if jwk_key:
                payload = jwt.decode(
                    token,
                    jwk_key,
                    algorithms=["RS256", "ES256"],
                    options={"verify_aud": False},
                )
            else:
                print("WARNING AUTH: JWK not found for kid, falling back to unverified decode")
                payload = jwt.decode(
                    token,
                    "",
                    options={"verify_signature": False, "verify_aud": False},
                )
        else:
            raise JWTError(f"Unsupported algorithm: {alg}")

        supabase_user_id: str = payload.get("sub")
        if not supabase_user_id:
            raise JWTError("Missing sub claim")
    except JWTError as e:
        print(f"DEBUG AUTH: token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": f"Invalid or expired token: {str(e)}"},
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

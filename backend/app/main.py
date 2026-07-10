from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.config import settings
from app.api.v1.router import v1_router
from app.utils.exceptions import ClarifyBaseError
from app.database import init_db

# Initialize Sentry if configured
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=1.0,
        environment=settings.APP_ENV,
    )

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Clarify AI - Upload Anything. Understand Everything. Enterprise Document Intelligence.",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    """Run database table creation on startup in development mode."""
    if settings.APP_ENV == "development":
        try:
            await init_db()
        except Exception:
            pass # Suppress if tables already initialized via migrations


@app.exception_handler(ClarifyBaseError)
async def clarify_error_handler(request: Request, exc: ClarifyBaseError):
    """Global exception handler converting custom exceptions to structured JSON responses."""
    status_map = {
        "UNAUTHORIZED": 401,
        "FORBIDDEN": 403,
        "NOT_FOUND": 404,
        "RATE_LIMIT_EXCEEDED": 429,
        "MONTHLY_LIMIT_REACHED": 429,
        "UPLOAD_TOO_LARGE": 400,
        "UNSUPPORTED_FILE_TYPE": 400,
        "ANALYSIS_FAILED": 500,
        "LLM_UNAVAILABLE": 503,
    }
    status_code = status_map.get(exc.code, 500)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all error handler shielding internal implementation details."""
    # Log the real traceback here or send to Sentry
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
            }
        },
    )


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


# Attach core API routers
app.include_router(v1_router, prefix="/v1")

import logging
import structlog
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.config import settings
from app.api.v1.router import v1_router
from app.utils.exceptions import ClarifyBaseError
from app.database import init_db


# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Standard logging setup
logging.basicConfig(
    format="%(message)s",
    stream=None,
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
)

# Sentry logging integration
if settings.SENTRY_DSN:
    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR
    )
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration(), sentry_logging],
        traces_sample_rate=1.0,
        environment=settings.APP_ENV,
    )

logger = structlog.get_logger()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Clarify AI - Upload Anything. Understand Everything. Enterprise Document Intelligence.",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
)


class LimitUploadSize(BaseHTTPMiddleware):
    """Limit upload size to prevent DoS via large request bodies."""
    
    def __init__(self, app, max_size: int):
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and request.url.path.endswith("/uploads"):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_size + 1024 * 1024:  # +1MB buffer
                logger.warning("upload_size_exceeded", 
                    path=request.url.path,
                    content_length=content_length,
                    max_size=self.max_size,
                    client_ip=request.client.host if request.client else None
                )
                return JSONResponse(
                    status_code=413,
                    content={"error": {"code": "UPLOAD_TOO_LARGE", "message": f"File too large. Max size: {self.max_size // (1024*1024)}MB"}}
                )
        return await call_next(request)


# Select LLM provider middleware
@app.middleware("http")
async def select_llm_provider(request: Request, call_next):
    from app.services.llm_service import active_llm_provider
    provider = request.headers.get("x-llm-provider", "gemini").lower()
    if provider not in ("gemini", "ollama"):
        provider = "gemini"
    token = active_llm_provider.set(provider)
    try:
        response = await call_next(request)
        return response
    finally:
        active_llm_provider.reset(token)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info("request_started",
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        logger.info("request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        return response
    except Exception as e:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.error("request_failed",
            method=request.method,
            path=request.url.path,
            error=str(e),
            duration_ms=duration_ms,
            exc_info=True
        )
        raise


# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request size limit middleware (must be added before other middleware that reads body)
app.add_middleware(LimitUploadSize, max_size=settings.max_file_bytes)


@app.on_event("startup")
async def on_startup():
    """Run database table creation on startup in development mode."""
    logger.info("application_startup", env=settings.APP_ENV, version=settings.APP_VERSION)
    if settings.APP_ENV == "development":
        try:
            await init_db()
            logger.info("database_initialized")
        except Exception as e:
            logger.warning("database_init_skipped", error=str(e))


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
    
    logger.warning("clarify_error",
        code=exc.code,
        message=exc.message,
        path=request.url.path,
        status_code=status_code
    )
    
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
    logger.exception("unhandled_exception",
        path=request.url.path,
        error=str(exc)
    )
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
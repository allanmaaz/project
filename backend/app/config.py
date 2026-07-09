from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_ENV: str = "development"
    DEBUG: bool = False
    APP_NAME: str = "Clarify AI"
    APP_VERSION: str = "1.0.0"

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # Database
    DATABASE_URL: str = ""

    # AI — Gemini (FREE)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_FAST: str = "gemini-1.5-flash"      # for classification, suggestions
    GEMINI_MODEL_FULL: str = "gemini-1.5-flash"      # for full analysis
    GEMINI_MAX_OUTPUT_TOKENS: int = 8192
    GEMINI_TEMPERATURE: float = 0.2

    # File limits
    MAX_FILE_SIZE_MB: int = 20
    MAX_PDF_SIZE_MB: int = 50
    FREE_PLAN_MONTHLY_UPLOADS: int = 10

    # Rate limiting (simple in-memory, no Redis)
    RATE_LIMIT_UPLOADS_FREE: int = 10     # per hour
    RATE_LIMIT_CHAT_FREE: int = 50        # per hour

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Monitoring
    SENTRY_DSN: str = ""

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def max_file_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def max_pdf_bytes(self) -> int:
        return self.MAX_PDF_SIZE_MB * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

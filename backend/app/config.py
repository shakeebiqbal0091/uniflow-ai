try:
    from pydantic import BaseSettings
except Exception:
    from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./uniflow.db"
    JWT_SECRET: str = "change_me"
    ADMIN_EMAIL: str | None = None
    ADMIN_PASSWORD: str | None = None

    # Comma-separated list of allowed origins for CORS, e.g.
    # "http://localhost:5500,http://127.0.0.1:5500". Defaults to "*" for
    # local development (frontend/chat.html opened as file:// sends
    # Origin: null, which "*" matches). Tighten this before deploying.
    CORS_ALLOWED_ORIGINS_RAW: str = "*"

    @property
    def CORS_ALLOWED_ORIGINS(self) -> list[str]:
        return [o.strip() for o in self.CORS_ALLOWED_ORIGINS_RAW.split(",") if o.strip()]

    class Config:
        env_file = ".env"

settings = Settings()
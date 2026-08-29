try:
    from pydantic import BaseSettings
except Exception:
    from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./uniflow.db"
    JWT_SECRET: str = "change_me"
    ADMIN_EMAIL: str | None = None
    ADMIN_PASSWORD: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()

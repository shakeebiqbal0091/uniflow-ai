from fastapi import FastAPI
from backend.app.api.routes import requests as requests_router
from backend.app.api.routes import auth as auth_router
from backend.app.api.routes import register as register_router
from backend.app.api.routes import admin as admin_router
from backend.app.api.routes import chat as chat_router
from backend.app.config import settings
from backend.app.db.session import AsyncSessionLocal
from backend.app.services.auth_service import get_user_by_email, create_user

import asyncio
from backend.app.api.routes import protected as protected_router

app = FastAPI(title="UniFlow AI - Backend")


@app.get("/")
async def root():
    return {"status": "ok", "service": "uniflow-ai-backend"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


app.include_router(requests_router.router, prefix="/api/requests", tags=["requests"])
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(register_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(admin_router.router, prefix="/api/admin", tags=["admin"])
app.include_router(chat_router.router, prefix="/api/chat", tags=["chat"])
app.include_router(protected_router.router, prefix="/api/protected", tags=["protected"])


@app.on_event("startup")
async def seed_admin():
    # NOTE: Database schema is managed by Alembic migrations.
    # This startup hook only seeds an admin user when the DB exists and the
    # `ADMIN_EMAIL` and `ADMIN_PASSWORD` env vars are provided.
    if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
        return
    async with AsyncSessionLocal() as session:
        existing = await get_user_by_email(session, settings.ADMIN_EMAIL)
        if existing:
            return
        # create admin user
        await create_user(session, settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD, full_name="Admin", role="SUPER_ADMIN")

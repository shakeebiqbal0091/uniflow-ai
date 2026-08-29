from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# The frontend (frontend/chat.html) is a static file, so it's typically
# opened as file:// or served from a dev port different from the API's
# 127.0.0.1:8000 — that makes every request cross-origin and triggers a
# CORS preflight (OPTIONS) before the real POST. Without this middleware,
# FastAPI has no OPTIONS handler on these routes and returns 405, which
# blocks the preflight and silently breaks login/register/chat from the
# browser. allow_credentials=False is safe here since the frontend sends
# auth via an `Authorization: Bearer` header, not cookies.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
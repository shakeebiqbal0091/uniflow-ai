"""
Tests for Phase 3: AI Agent Chat Endpoint
"""

import pytest
from fastapi.testclient import TestClient
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.api.dependencies import get_db
from backend.app.db.session import Base
from backend.app.main import app
from backend.app.services.auth_service import create_user


@pytest.fixture
def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(init_db())

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


def test_student_can_send_chat_message(client):
    """Test that a student can send a message to the chat agent."""
    reg = client.post(
        "/api/auth/register",
        json={"email": "student@example.com", "password": "password123", "full_name": "Test Student"},
    )
    assert reg.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={"username": "student@example.com", "password": "password123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Send a chat message
    chat_resp = client.post(
        "/api/chat/",
        json={"content": "I need help with my transcript request"},
        headers=headers,
    )
    assert chat_resp.status_code == 200, chat_resp.text
    body = chat_resp.json()
    assert "message" in body
    assert "agent" in body
    assert body["agent"] == "student_services"


def test_chat_requires_authentication(client):
    """Test that chat endpoint requires authentication."""
    chat_resp = client.post(
        "/api/chat/",
        json={"content": "I need help"},
    )
    assert chat_resp.status_code == 401


def test_chat_rejects_empty_message(client):
    """Test that empty messages are rejected."""
    reg = client.post(
        "/api/auth/register",
        json={"email": "student2@example.com", "password": "password123", "full_name": "Test Student 2"},
    )
    assert reg.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={"username": "student2@example.com", "password": "password123"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Send empty message
    chat_resp = client.post(
        "/api/chat/",
        json={"content": "   "},
        headers=headers,
    )
    assert chat_resp.status_code == 400

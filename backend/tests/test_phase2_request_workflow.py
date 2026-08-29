import asyncio

import pytest  # pyright: ignore[reportMissingImports]
from fastapi.testclient import TestClient
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
    app.state.test_session_factory = session_factory
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    app.state.test_session_factory = None
    asyncio.run(engine.dispose())


def test_student_can_create_and_list_own_request(client):
    reg = client.post(
        "/api/auth/register",
        json={"email": "student@example.com", "password": "password123", "full_name": "Student User"},
    )
    assert reg.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={"username": "student@example.com", "password": "password123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post(
        "/api/requests/",
        json={
            "request_type": "transcript",
            "title": "Transcript Request",
            "description": "Need transcript for scholarship",
        },
        headers=headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    body = create_resp.json()
    assert body["status"] == "NEW"
    assert body["student_id"]

    list_resp = client.get("/api/requests/", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["title"] == "Transcript Request"


def test_admin_can_assign_and_update_request_status(client):
    async def seed_admin_user():
        async with app.state.test_session_factory() as session:
            user = await create_user(session, "admin@example.com", "password123", full_name="Admin User", role="ADMIN")
            await session.refresh(user)
            return user

    asyncio.run(seed_admin_user())

    reg = client.post(
        "/api/auth/register",
        json={"email": "student2@example.com", "password": "password123", "full_name": "Student User 2"},
    )
    assert reg.status_code == 201

    student_login = client.post(
        "/api/auth/login",
        json={"username": "student2@example.com", "password": "password123"},
    )
    assert student_login.status_code == 200, student_login.text
    student_headers = {"Authorization": f"Bearer {student_login.json()['access_token']}"}

    request_resp = client.post(
        "/api/requests/",
        json={
            "request_type": "fee_issue",
            "title": "Fee issue",
            "description": "Paid but portal shows unpaid",
        },
        headers=student_headers,
    )
    assert request_resp.status_code == 201, request_resp.text
    request_id = request_resp.json()["id"]

    admin_login = client.post(
        "/api/auth/login",
        json={"username": "admin@example.com", "password": "password123"},
    )
    assert admin_login.status_code == 200, admin_login.text
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    assign_resp = client.patch(
        f"/api/admin/requests/{request_id}/assign",
        json={"assigned_to": "finance-team", "department_id": "finance"},
        headers=admin_headers,
    )
    assert assign_resp.status_code == 200, assign_resp.text
    assert assign_resp.json()["assigned_to"] == "finance-team"
    assert assign_resp.json()["department_id"] == "finance"

    status_resp = client.patch(
        f"/api/admin/requests/{request_id}/status",
        json={"status": "IN_PROGRESS"},
        headers=admin_headers,
    )
    assert status_resp.status_code == 200, status_resp.text
    assert status_resp.json()["status"] == "IN_PROGRESS"

    admin_list = client.get("/api/admin/requests", headers=admin_headers)
    assert admin_list.status_code == 200, admin_list.text
    assert any(item["id"] == request_id for item in admin_list.json())

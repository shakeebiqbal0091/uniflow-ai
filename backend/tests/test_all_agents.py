"""
Tests for all 7 agents
"""

import pytest
from fastapi.testclient import TestClient
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.api.dependencies import get_db
from backend.app.db.session import Base
from backend.app.main import app


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


def setup_student(client):
    """Helper to register and login a student."""
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
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


class TestAgentRouting:
    """Test that the orchestrator correctly routes to different agents based on intent."""

    def test_student_services_agent(self, client):
        """Test routing to Student Services Agent."""
        headers = setup_student(client)

        resp = client.post(
            "/api/chat/",
            json={"content": "I need help with my transcript request"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        # Student Services Agent is default
        assert body["agent"] in ["student_services", "orchestrator"]

    def test_finance_agent_routing(self, client):
        """Test routing to Finance Agent based on 'fee' keyword."""
        headers = setup_student(client)

        resp = client.post(
            "/api/chat/",
            json={"content": "What is my current fee balance?"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["agent"] == "finance"

    def test_finance_agent_payment_keyword(self, client):
        """Test Finance Agent routing with 'payment' keyword."""
        headers = setup_student(client)

        resp = client.post(
            "/api/chat/",
            json={"content": "I made a payment yesterday but it shows as pending"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["agent"] == "finance"

    def test_enrollment_agent_routing(self, client):
        """Test routing to Enrollment Agent based on 'course' keyword."""
        headers = setup_student(client)

        resp = client.post(
            "/api/chat/",
            json={"content": "How do I register for a database course?"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["agent"] == "enrollment"

    def test_enrollment_agent_prerequisite_keyword(self, client):
        """Test Enrollment Agent routing with 'prerequisite' keyword."""
        headers = setup_student(client)

        resp = client.post(
            "/api/chat/",
            json={"content": "Do I have the prerequisites for advanced algorithms?"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["agent"] == "enrollment"

    def test_document_agent_routing(self, client):
        """Test routing to Document Agent based on 'document' keyword."""
        headers = setup_student(client)

        resp = client.post(
            "/api/chat/",
            json={"content": "I uploaded my degree certificate. Can you verify it?"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["agent"] == "document"

    def test_support_agent_routing(self, client):
        """Test routing to Support Agent based on 'complaint' keyword."""
        headers = setup_student(client)

        resp = client.post(
            "/api/chat/",
            json={"content": "The classroom has had no internet for 3 days. This is a major issue."},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["agent"] == "support"

    def test_support_agent_problem_keyword(self, client):
        """Test Support Agent routing with 'problem' keyword."""
        headers = setup_student(client)

        resp = client.post(
            "/api/chat/",
            json={"content": "I have a problem accessing the online portal"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["agent"] == "support"

    def test_policy_agent_routing(self, client):
        """Test routing to Policy Agent based on 'policy' keyword."""
        headers = setup_student(client)

        resp = client.post(
            "/api/chat/",
            json={"content": "What is the attendance policy for this semester?"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["agent"] == "policy"

    def test_policy_agent_regulation_keyword(self, client):
        """Test Policy Agent routing with 'regulation' keyword."""
        headers = setup_student(client)

        resp = client.post(
            "/api/chat/",
            json={"content": "Can you explain the academic integrity regulations?"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["agent"] == "policy"

    def test_orchestrator_get_available_agents(self, client):
        """Test that orchestrator reports all available agents."""
        from backend.app.agents.orchestrator import OrchestratorAgent
        from backend.app.db.session import AsyncSessionLocal

        async def check_agents():
            async with AsyncSessionLocal() as db:
                orch = OrchestratorAgent(db, "test-user-id")
                agents = orch.get_available_agents()
                return agents

        agents = asyncio.run(check_agents())
        assert "student_services" in agents
        assert "finance" in agents
        assert "enrollment" in agents
        assert "document" in agents
        assert "support" in agents
        assert "policy" in agents
        assert len(agents) == 6

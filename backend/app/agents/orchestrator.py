"""
Orchestrator Agent

Coordinates between different specialized agents and manages workflows.

Flow:
1. User sends request
2. Orchestrator analyzes intent
3. Routes to appropriate agent (Student Services, Finance, Enrollment, etc)
4. Receives result from agent
5. Returns response to user
"""

from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.student_agent import StudentServicesAgent
from backend.app.agents.finance_agent import FinanceAgent
from backend.app.agents.enrollment_agent import EnrollmentAgent
from backend.app.agents.document_agent import DocumentAgent
from backend.app.agents.support_agent import SupportAgent
from backend.app.agents.policy_agent import PolicyAgent


class OrchestratorAgent:
    """Main orchestrator that routes requests to specialized agents."""

    def __init__(self, db: AsyncSession, current_user_id: str):
        self.db = db
        self.current_user_id = current_user_id
        self.student_agent = StudentServicesAgent(db, current_user_id)
        self.finance_agent = FinanceAgent(db, current_user_id)
        self.enrollment_agent = EnrollmentAgent(db, current_user_id)
        self.document_agent = DocumentAgent(db, current_user_id)
        self.support_agent = SupportAgent(db, current_user_id)
        self.policy_agent = PolicyAgent(db, current_user_id)

    async def process_request(self, user_message: str) -> dict[str, Any]:
        """
        Process a user request by routing to the appropriate agent.

        Args:
            user_message: Natural language request from user

        Returns:
            Response from the appropriate agent
        """

        # Simple intent classification based on keywords
        # In Phase 4, this should use actual LLM-based intent classification
        message_lower = user_message.lower()

        if any(word in message_lower for word in ["fee", "payment", "invoice", "balance"]):
            return await self.finance_agent.process_request(user_message)
        elif any(
            word in message_lower
            for word in ["course", "register", "enrollment", "prerequisite"]
        ):
            return await self.enrollment_agent.process_request(user_message)
        elif any(
            word in message_lower
            for word in ["document", "upload", "certificate", "diploma"]
        ):
            return await self.document_agent.process_request(user_message)
        elif any(
            word in message_lower
            for word in ["complain", "problem", "issue", "broken", "complaint"]
        ):
            return await self.support_agent.process_request(user_message)
        elif any(
            word in message_lower
            for word in ["policy", "rule", "regulation", "requirement"]
        ):
            return await self.policy_agent.process_request(user_message)
        else:
            # Default to student services agent
            return await self.student_agent.process_request(user_message)

    def get_available_agents(self) -> list[str]:
        """Get list of available agents."""
        return [
            "student_services",
            "finance",
            "enrollment",
            "document",
            "policy",
            "support",
        ]

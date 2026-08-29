"""
Agent system for UniFlow AI.

Agents are autonomous AI workers that can:
- Understand requests
- Use tools to access data
- Make decisions
- Execute workflows
- Escalate to humans when needed
"""

from backend.app.agents.orchestrator import OrchestratorAgent
from backend.app.agents.student_agent import StudentServicesAgent
from backend.app.agents.finance_agent import FinanceAgent
from backend.app.agents.enrollment_agent import EnrollmentAgent
from backend.app.agents.document_agent import DocumentAgent
from backend.app.agents.support_agent import SupportAgent
from backend.app.agents.policy_agent import PolicyAgent

__all__ = [
    "OrchestratorAgent",
    "StudentServicesAgent",
    "FinanceAgent",
    "EnrollmentAgent",
    "DocumentAgent",
    "SupportAgent",
    "PolicyAgent",
]

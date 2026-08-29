"""
Support Agent

Handles support-related requests:
- Student complaints
- IT issues
- Facilities issues
- Ticket creation
- Escalation to human administrators
"""

from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.tools import AgentTools


class SupportAgent:
    """Agent for handling student support and complaints."""

    def __init__(self, db: AsyncSession, current_user_id: str):
        self.db = db
        self.current_user_id = current_user_id
        self.tools = AgentTools(db, current_user_id)

    async def process_request(self, user_message: str) -> dict[str, Any]:
        """
        Process a support or complaint request.

        Responsibilities:
        - Classify issues (IT, facilities, academic, etc)
        - Assess priority
        - Create support tickets
        - Escalate to appropriate department
        """

        return {
            "status": "success",
            "agent": "support",
            "message": f"Support Agent received your request: {user_message[:50]}...",
            "next_steps": ["issue_classification", "ticket_creation"],
        }

    async def execute_tool(self, tool_name: str, tool_input: dict) -> dict[str, Any]:
        """Execute a support tool with the given input."""
        try:
            if tool_name == "create_support_ticket":
                return await self.tools.create_support_ticket(
                    student_id=tool_input.get("student_id"),
                    category=tool_input.get("category"),
                    title=tool_input.get("title"),
                    description=tool_input.get("description"),
                    priority=tool_input.get("priority", "NORMAL"),
                )
            elif tool_name == "get_issue_status":
                return await self.tools.get_issue_status(
                    tool_input.get("student_id")
                )
            elif tool_name == "classify_issue":
                # No standalone classifier — category is currently supplied
                # by the caller/LLM and passed straight into create_support_ticket().
                return {"error": "Issue classification not yet implemented"}
            elif tool_name == "assess_priority":
                # Same as above — priority is caller-supplied, not inferred yet.
                return {"error": "Priority assessment not yet implemented"}
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
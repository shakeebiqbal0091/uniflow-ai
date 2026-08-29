"""
Enrollment Agent

Handles enrollment-related requests:
- Course eligibility verification
- Registration workflow guidance
- Prerequisite checking
- Admission-related requests
"""

from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.tools import AgentTools


class EnrollmentAgent:
    """Agent for enrollment and course-related services."""

    def __init__(self, db: AsyncSession, current_user_id: str):
        self.db = db
        self.current_user_id = current_user_id
        self.tools = AgentTools(db, current_user_id)

    async def process_request(self, user_message: str) -> dict[str, Any]:
        """
        Process a student enrollment request.

        Responsibilities:
        - Check course eligibility
        - Verify prerequisites
        - Explain registration process
        - Answer enrollment questions
        """

        return {
            "status": "success",
            "agent": "enrollment",
            "message": f"Enrollment Agent received your request: {user_message[:50]}...",
            "next_steps": ["eligibility_check", "prerequisite_verification"],
        }

    async def execute_tool(self, tool_name: str, tool_input: dict) -> dict[str, Any]:
        """Execute an enrollment tool with the given input."""
        try:
            if tool_name == "check_course_eligibility":
                # TODO: Implement course eligibility check
                return {"error": "Course eligibility check not yet implemented"}
            elif tool_name == "verify_prerequisites":
                # TODO: Implement prerequisite verification
                return {"error": "Prerequisite verification not yet implemented"}
            elif tool_name == "get_enrollment_status":
                # TODO: Implement enrollment status retrieval
                return {"error": "Enrollment status lookup not yet implemented"}
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}

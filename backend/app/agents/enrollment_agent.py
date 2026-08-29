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
                return await self.tools.check_course_eligibility(
                    tool_input.get("student_id"), tool_input.get("course_code")
                )
            elif tool_name == "get_course_details":
                return await self.tools.get_course_details(
                    tool_input.get("course_code")
                )
            elif tool_name == "verify_prerequisites":
                # No standalone prerequisite check — check_course_eligibility()
                # already validates prerequisites as part of eligibility.
                return await self.tools.check_course_eligibility(
                    tool_input.get("student_id"), tool_input.get("course_code")
                )
            elif tool_name == "get_enrollment_status":
                return await self.tools.get_enrollment_status(
                    tool_input.get("student_id")
                )
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
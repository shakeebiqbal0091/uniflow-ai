"""
Student Services Agent

Handles student requests including:
- Transcript requests
- Fee inquiries
- Enrollment questions
- General student assistance
"""

from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI
import json

from backend.app.agents.tools import AgentTools, AGENT_TOOLS


class StudentServicesAgent:
    """Agent for student-facing services."""

    def __init__(self, db: AsyncSession, current_user_id: str):
        self.db = db
        self.current_user_id = current_user_id
        self.tools = AgentTools(db, current_user_id)
        self.client = None  # Will be initialized with actual client in async context

    async def process_request(self, user_message: str) -> dict[str, Any]:
        """
        Process a student request using agentic reasoning.

        Flow:
        1. Student sends natural language request
        2. Agent understands intent
        3. Agent calls tools to gather information
        4. Agent decides next action
        5. Agent responds to student
        """

        messages = [
            {
                "role": "system",
                "content": """You are a helpful Student Services Agent for UniFlow AI University Operations.

Your responsibilities:
- Understand student requests in natural language
- Use available tools to retrieve student information and create requests
- Provide clear, helpful responses
- Ask clarifying questions when needed
- Be professional and courteous

Always be truthful about what you can do. If you cannot help with something, explain why.
""",
            },
            {"role": "user", "content": user_message},
        ]

        return {
            "status": "success",
            "agent": "student_services",
            "message": "Student request received and understood. (Full agent execution to be implemented with OpenAI client)",
            "next_steps": ["tool_calling", "response_generation"],
        }

    async def execute_tool(self, tool_name: str, tool_input: dict) -> dict[str, Any]:
        """Execute a tool with the given input."""
        try:
            if tool_name == "get_student_profile":
                return await self.tools.get_student_profile(
                    tool_input.get("student_id")
                )
            elif tool_name == "get_student_requests":
                return await self.tools.get_student_requests(
                    tool_input.get("student_id"), tool_input.get("status")
                )
            elif tool_name == "get_request_details":
                return await self.tools.get_request_details(
                    tool_input.get("request_id")
                )
            elif tool_name == "create_service_request":
                return await self.tools.create_service_request(
                    student_id=tool_input.get("student_id"),
                    request_type=tool_input.get("request_type"),
                    title=tool_input.get("title"),
                    description=tool_input.get("description"),
                    priority=tool_input.get("priority", "normal"),
                )
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}

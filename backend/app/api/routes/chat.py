"""
Chat API endpoint for interacting with AI agents.

Provides:
- POST /api/chat - Send a message to the agent and get a response
- GET /api/chat/history - Get conversation history (future)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, Any

from backend.app.api.dependencies import get_db
from backend.app.api.security import get_current_user
from backend.app.agents.orchestrator import OrchestratorAgent
from backend.app.db import models

router = APIRouter()


class ChatMessage(BaseModel):
    """A message in the chat conversation."""

    content: str
    agent: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from the chat API."""

    message: str
    agent: str
    next_steps: Optional[list[str]] = None
    data: Optional[dict[str, Any]] = None


@router.post("/", response_model=ChatResponse)
async def send_chat_message(
    payload: ChatMessage,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Send a message to the AI agent and get a response.

    The agent will:
    1. Understand your request
    2. Use tools to retrieve information
    3. Take appropriate actions
    4. Respond with helpful information or next steps
    """

    if not payload.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty",
        )

    try:
        # Initialize orchestrator with current user context
        orchestrator = OrchestratorAgent(db, str(current_user.id))

        # Process the request
        result = await orchestrator.process_request(payload.content)

        return ChatResponse(
            message=result.get("message", ""),
            agent=result.get("agent", "orchestrator"),
            next_steps=result.get("next_steps"),
            data=result.get("data"),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent processing failed: {str(e)}",
        )

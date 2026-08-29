"""
UniFlow AI - Agent Usage Guide

This guide shows how to use the 7-agent system.
"""

# ============================================================================
# QUICK START - TEST THE AGENTS
# ============================================================================

# 1. Start the API server
# $ python -m uvicorn backend.app.main:app --reload

# 2. Register and login (or use existing credentials)
# POST http://localhost:8000/api/auth/register
# {
#   "email": "student@example.com",
#   "password": "password123",
#   "full_name": "Test Student"
# }

# 3. Login to get token
# POST http://localhost:8000/api/auth/login
# {
#   "username": "student@example.com",
#   "password": "password123"
# }

# 4. Use the Chat API with different requests (see examples below)
# POST http://localhost:8000/api/chat/
# Authorization: Bearer {access_token}
# Content-Type: application/json
# {
#   "content": "Your message here"
# }


# ============================================================================
# EXAMPLE CONVERSATIONS FOR EACH AGENT
# ============================================================================

EXAMPLE_CONVERSATIONS = {
    "finance_agent": [
        "What is my current fee balance?",
        "I made a payment yesterday but the portal shows it as pending",
        "Can you explain the fee structure for international students?",
        "When is my next payment due?",
    ],
    "enrollment_agent": [
        "How do I register for the Advanced Database course?",
        "Do I have the prerequisites for Data Science?",
        "Can I take four courses next semester?",
        "What are the requirements for my major?",
    ],
    "document_agent": [
        "I uploaded my degree certificate. Is it valid?",
        "Can you verify my identity documents?",
        "What documents do I need for admission?",
        "I uploaded my transcript and CNIC",
    ],
    "support_agent": [
        "The classroom has had no internet for three days",
        "I can't access the online portal",
        "My laptop broke and I need to use lab computers",
        "There's a problem with the library WiFi",
    ],
    "policy_agent": [
        "What's the attendance policy?",
        "Can you explain the academic integrity rules?",
        "What are the late submission penalties?",
        "When can I drop a course?",
    ],
    "student_services_agent": [
        "I need help with my request",
        "Can you help me?",
        "General question about university services",
        "Hello, I need assistance",
    ],
}


# ============================================================================
# USING THE AGENTS PROGRAMMATICALLY
# ============================================================================

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.agents import OrchestratorAgent

async def example_usage():
    """Example of using agents programmatically."""
    
    # Get database session (in real app, this comes from FastAPI dependency)
    # db = ...
    
    # Initialize orchestrator
    # orchestrator = OrchestratorAgent(db, current_user_id="student123")
    
    # Send a request
    # response = await orchestrator.process_request(
    #     "What's my current fee balance?"
    # )
    
    # Response format:
    # {
    #     "status": "success",
    #     "agent": "finance",
    #     "message": "Finance Agent received your request...",
    #     "next_steps": ["fee_lookup", "payment_verification"]
    # }
    
    pass


# ============================================================================
# AGENT SELECTION LOGIC
# ============================================================================

# The orchestrator uses simple keyword matching to route requests:

ROUTING_RULES = {
    "finance": {
        "keywords": ["fee", "payment", "invoice", "balance", "refund"],
        "agent": "FinanceAgent",
    },
    "enrollment": {
        "keywords": ["course", "register", "enrollment", "prerequisite"],
        "agent": "EnrollmentAgent",
    },
    "document": {
        "keywords": ["document", "upload", "certificate", "diploma"],
        "agent": "DocumentAgent",
    },
    "support": {
        "keywords": ["complaint", "problem", "issue", "broken"],
        "agent": "SupportAgent",
    },
    "policy": {
        "keywords": ["policy", "rule", "regulation", "requirement"],
        "agent": "PolicyAgent",
    },
}

# Default fallback:
# If no keywords match → StudentServicesAgent


# ============================================================================
# TESTING THE AGENTS
# ============================================================================

# Run all agent tests:
# $ python -m pytest backend/tests/test_all_agents.py -v

# Run specific agent test:
# $ python -m pytest backend/tests/test_all_agents.py::TestAgentRouting::test_finance_agent_routing -v

# Run all tests:
# $ python -m pytest backend/tests/ -v


# ============================================================================
# EXTENDING AN AGENT
# ============================================================================

# Example: Adding a real tool to Finance Agent

# 1. Add tool to AgentTools (in backend/app/agents/tools.py)
#    @staticmethod
#    async def get_fee_balance(student_id: str) -> dict:
#        # Validate authorization
#        # Query database
#        # Return structured result

# 2. Update agent process_request() to call the tool
#    async def process_request(self, user_message: str) -> dict:
#        # Use LLM to understand request
#        # Call get_fee_balance tool
#        # Format response

# 3. Add test case
#    def test_finance_agent_fee_balance(self, client):
#        # Mock a finance request
#        # Verify correct tool is called

# 4. Run tests to verify
#    $ python -m pytest


# ============================================================================
# ORCHESTRATOR AGENT DETAILS
# ============================================================================

"""
The OrchestratorAgent serves as the main entry point.

Its responsibilities:
1. Receive user request
2. Analyze intent (currently: keyword matching)
3. Select appropriate agent
4. Route request to that agent
5. Return agent response

Current routing (Phase 4):
- Keyword-based (fast, deterministic)

Future routing (Phase 5):
- LLM-based classifier (higher accuracy)
- Confidence scores
- Human fallback

The orchestrator instantiates all 6 specialized agents:
- StudentServicesAgent
- FinanceAgent
- EnrollmentAgent
- DocumentAgent
- SupportAgent
- PolicyAgent

And provides:
- get_available_agents() - list of agents
- process_request(message) - route to agent
"""


# ============================================================================
# AUTHORIZATION MODEL
# ============================================================================

"""
Every tool enforces authorization:

1. Tool receives current_user_id from agent
2. Tool validates user has permission to access data
3. Example: get_fee_balance(student_id)
   - Verifies student_id matches current_user
   - Only admins can query other students

Authorization levels:
- STUDENT: Only own data
- STAFF: Department data
- DEPARTMENT_ADMIN: All students in department
- FINANCE_ADMIN: All financial records
- SUPER_ADMIN: All data

This is enforced in tool functions, not in agents.
"""


# ============================================================================
# RESPONSE FORMAT
# ============================================================================

RESPONSE_FORMAT = {
    "status": "success",  # or "error"
    "agent": "finance",   # which agent handled it
    "message": "Your current fee balance is...",  # user-facing
    "next_steps": ["fee_lookup", "payment_verification"],  # actions
}


# ============================================================================
# DEBUGGING
# ============================================================================

# Enable logging:
import logging
logging.basicConfig(level=logging.DEBUG)

# Check which agent is selected:
# - Watch logs for "routing to {agent_name}"
# - Verify keywords in routing logic match your request

# Run agent directly:
# from backend.app.agents import FinanceAgent
# agent = FinanceAgent(db, user_id)
# result = await agent.process_request("What's my fee?")

# Check orchestrator routing:
# from backend.app.agents import OrchestratorAgent
# orch = OrchestratorAgent(db, user_id)
# agents = orch.get_available_agents()
# print(agents)  # Shows: [student_services, finance, enrollment, document, support, policy]

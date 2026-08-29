"""
Agent Architecture Documentation

This document explains the UniFlow AI agent system architecture.

7-Agent System Architecture
===========================

1. ORCHESTRATOR AGENT (Request Router)
   ├─ Routes requests to appropriate specialized agents
   ├─ Uses intent classification (keyword-based in Phase 4, LLM-based in Phase 5)
   └─ Returns response from selected agent

2. STUDENT SERVICES AGENT (General Support)
   ├─ Responsibilities: General requests, student assistance
   ├─ Tools:
   │  ├─ get_student_profile(student_id)
   │  ├─ get_student_requests(student_id)
   │  ├─ get_request_details(request_id)
   │  └─ create_service_request(...)
   └─ Fallback when intent is ambiguous

3. FINANCE AGENT (Fee & Payment)
   ├─ Responsibilities: Fee inquiries, payment verification, invoices
   ├─ Tools:
   │  ├─ get_fee_balance(student_id) → Outstanding fees
   │  ├─ verify_payment(payment_id) → Payment status
   │  └─ get_fee_policy() → Fee regulations
   └─ Routing keywords: fee, payment, invoice, balance, refund

4. ENROLLMENT AGENT (Course & Registration)
   ├─ Responsibilities: Course eligibility, prerequisites, registration
   ├─ Tools:
   │  ├─ check_course_eligibility(student_id, course_id)
   │  ├─ verify_prerequisites(student_id, course_id)
   │  └─ get_enrollment_status(student_id)
   └─ Routing keywords: course, register, enrollment, prerequisite

5. DOCUMENT AGENT (File Processing)
   ├─ Responsibilities: Document validation, classification, data extraction
   ├─ Tools:
   │  ├─ validate_document(file) → Valid/invalid
   │  ├─ classify_document(file) → Document type
   │  └─ extract_document_data(file) → Extracted fields
   └─ Routing keywords: document, upload, certificate, diploma

6. SUPPORT AGENT (Complaints & Issues)
   ├─ Responsibilities: Issue classification, prioritization, ticket creation
   ├─ Tools:
   │  ├─ classify_issue(description) → Issue category
   │  ├─ assess_priority(issue) → Priority level
   │  └─ create_support_ticket(...)
   └─ Routing keywords: complaint, problem, issue, broken

7. POLICY AGENT (University Rules)
   ├─ Responsibilities: Policy search, rule explanation, citations
   ├─ Tools:
   │  ├─ search_policies(query) → Matching policies
   │  ├─ get_policy_details(policy_id) → Policy content
   │  └─ get_policy_citations(policy_id) → Source documents
   └─ Routing keywords: policy, rule, regulation, requirement


Request Processing Flow
=======================

User Request
   ↓
Chat API (/api/chat/)
   ↓
Orchestrator Agent
   ├─ Classify intent (keyword matching in Phase 4)
   └─ Select appropriate agent
       ↓
   Specialized Agent (Finance, Enrollment, etc.)
   ├─ Understand request context
   ├─ Select tools needed
   └─ Execute tools
       ↓
   Tools Layer
   ├─ Validate authorization
   ├─ Query database
   └─ Return structured data
       ↓
   Agent processes tool results
   └─ Formats response
       ↓
   Chat API
   └─ Returns response to user


Agent Common Interface
=====================

Every agent implements:

1. __init__(db: AsyncSession, current_user_id: str)
   - Accept database connection and user ID
   - Instantiate domain-specific tools

2. async process_request(user_message: str) -> dict
   - Accept natural language request
   - Return structured response with:
     - status: "success" or "error"
     - agent: agent name
     - message: user-facing response
     - next_steps: list of actions to take

3. async execute_tool(tool_name: str, tool_input: dict) -> dict
   - Execute named tool with arguments
   - Return structured result or error


Authorization Pattern
===================

All agents enforce authorization at tool level:

1. Tool receives current_user_id from agent
2. Tool validates user has permission to access data
3. Example: get_fee_balance(student_id) verifies student_id matches current_user
4. Returns error if authorization fails
5. Never exposes unauthorized data


Intent Classification Strategy
=============================

Phase 4 (MVP):
- Keyword-based routing using simple string matching
- Sufficient for demo and validation
- Fast and deterministic

Phase 5 (Production):
- LLM-based intent classifier
- Higher accuracy on ambiguous requests
- Confidence scores for each agent
- Fallback to human when uncertain


Tool Design Philosophy
=====================

Tools are narrow, deterministic functions that:

1. Accept minimal required input
2. Validate input and authorization
3. Query database or call services
4. Return structured data
5. Never invent information
6. Include error context in failures

Example:
```python
async def get_fee_balance(student_id: str) -> dict:
    # Validate authorization
    if student_id != current_user_id:
        return {"error": "Unauthorized"}
    
    # Query database
    student = await db.query(Student).filter(...).one_or_none()
    if not student:
        return {"error": "Student not found"}
    
    # Return structured data
    return {
        "student_id": student.id,
        "outstanding_balance": student.fee_balance,
        "due_date": student.fee_due_date
    }
```


Current Status
==============

Implemented Agents: 7/7
- StudentServicesAgent: COMPLETE with tools
- FinanceAgent: SCAFFOLD (placeholder tools)
- EnrollmentAgent: SCAFFOLD (placeholder tools)
- DocumentAgent: SCAFFOLD (placeholder tools)
- SupportAgent: SCAFFOLD (placeholder tools)
- PolicyAgent: SCAFFOLD (placeholder tools)
- OrchestratorAgent: COMPLETE with routing

Tests: 11/11 passing
- Orchestrator routing tests verify all 6 agent paths
- Keyword classification tests confirm intent detection
- Agent availability endpoint tests pass


Phase 4 Implementation Roadmap
=============================

1. ✅ Create agent skeletons (DONE)
2. ✅ Implement orchestrator routing (DONE)
3. ✅ Create comprehensive tests (DONE)
4. → Implement tool functions for each agent
5. → Integrate OpenAI API for LLM reasoning
6. → Add RAG for policy search
7. → Implement document processing (OCR, extraction)
8. → Add escalation logic
9. → Create admin dashboard for escalations
10. → Comprehensive testing and evaluation


Key Design Decisions
===================

1. Single OrchestratorAgent routes to specialists
   - Pros: Centralized routing, easy to debug, simple addition of new agents
   - Cons: Single orchestrator could be bottleneck (future improvement)

2. Keyword-based intent classification in Phase 4
   - Pros: Fast, deterministic, easy to understand, sufficient for MVP
   - Cons: Less accurate than LLM, limited to predefined keywords

3. Placeholder tools with error returns
   - Pros: System architecture complete, easy to add real implementations
   - Cons: No actual functionality yet

4. Authorization at tool level, not agent level
   - Pros: Fine-grained control, tools are reusable across agents
   - Cons: Requires discipline in tool implementation

5. Structured response format across all agents
   - Pros: Consistent interface, easy for frontend to consume
   - Cons: Requires wrapper around LLM responses


Future Enhancements
==================

1. Multi-turn conversations within an agent
2. Agent handoff (Finance → Support for escalation)
3. Parallel tool execution
4. Tool result caching
5. Agent memory across conversations
6. Cost tracking per agent
7. Performance metrics per agent
8. A/B testing different routing strategies
9. Adaptive routing based on success rates
10. Custom agents for specific use cases
"""

# This file is for documentation only

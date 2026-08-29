"""
Tools available to agents for accessing data and performing actions.

Tools are deterministic functions that bridge LLM reasoning to actual business logic.
They perform:
- Authorization checks
- Input validation
- Data retrieval
- Business logic enforcement

Agents cannot invent data; they must use tools to retrieve it.
"""

from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from uuid import UUID
from decimal import Decimal
import datetime

from backend.app.db import models
from backend.app.services.request_service import (
    create_request,
    get_request,
    list_requests,
)
from backend.app.schemas import ServiceRequestCreate


# ============================================================================
# TOOL DEFINITIONS FOR OPENAI FUNCTION CALLING
# ============================================================================

AGENT_TOOLS = [
    # Student Services Tools
    {
        "type": "function",
        "function": {
            "name": "get_student_profile",
            "description": "Get a student's profile information",
            "parameters": {
                "type": "object",
                "properties": {"student_id": {"type": "string"}},
                "required": ["student_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_student_requests",
            "description": "Get all service requests for a student",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string"},
                    "status": {"type": "string"},
                },
                "required": ["student_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_service_request",
            "description": "Create a new service request",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string"},
                    "request_type": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {"type": "string"},
                },
                "required": ["student_id", "request_type", "title"],
            },
        },
    },
    # Finance Tools
    {
        "type": "function",
        "function": {
            "name": "get_fee_balance",
            "description": "Get student's outstanding fee balance",
            "parameters": {
                "type": "object",
                "properties": {"student_id": {"type": "string"}},
                "required": ["student_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_payment_status",
            "description": "Get status of recent payments",
            "parameters": {
                "type": "object",
                "properties": {"student_id": {"type": "string"}},
                "required": ["student_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_invoice_details",
            "description": "Get details of unpaid invoices",
            "parameters": {
                "type": "object",
                "properties": {"student_id": {"type": "string"}},
                "required": ["student_id"],
            },
        },
    },
    # Enrollment Tools
    {
        "type": "function",
        "function": {
            "name": "check_course_eligibility",
            "description": "Check if student is eligible for a course",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string"},
                    "course_code": {"type": "string"},
                },
                "required": ["student_id", "course_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_course_details",
            "description": "Get details about a course",
            "parameters": {
                "type": "object",
                "properties": {"course_code": {"type": "string"}},
                "required": ["course_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_enrollment_status",
            "description": "Get student's enrollment status and courses",
            "parameters": {
                "type": "object",
                "properties": {"student_id": {"type": "string"}},
                "required": ["student_id"],
            },
        },
    },
    # Document Tools
    {
        "type": "function",
        "function": {
            "name": "validate_document",
            "description": "Validate an uploaded document",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {"type": "string"},
                    "document_type": {"type": "string"},
                },
                "required": ["document_id", "document_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_document_status",
            "description": "Get verification status of documents",
            "parameters": {
                "type": "object",
                "properties": {"student_id": {"type": "string"}},
                "required": ["student_id"],
            },
        },
    },
    # Support Tools
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": "Create a support/complaint ticket",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string"},
                    "category": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {"type": "string"},
                },
                "required": ["student_id", "category", "title", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_issue_status",
            "description": "Get status of support issues",
            "parameters": {
                "type": "object",
                "properties": {"student_id": {"type": "string"}},
                "required": ["student_id"],
            },
        },
    },
    # Policy Tools
    {
        "type": "function",
        "function": {
            "name": "search_policies",
            "description": "Search university policies",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_policy_details",
            "description": "Get full text of a policy",
            "parameters": {
                "type": "object",
                "properties": {"policy_id": {"type": "string"}},
                "required": ["policy_id"],
            },
        },
    },
]


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================


class AgentTools:
    """Tools available to agents."""

    def __init__(self, db: AsyncSession, current_user_id: str):
        self.db = db
        self.current_user_id = current_user_id

    # ========================================================================
    # STUDENT SERVICES TOOLS
    # ========================================================================

    async def get_student_profile(self, student_id: str) -> dict[str, Any]:
        """Get student profile information."""
        if student_id != self.current_user_id:
            return {"error": "Unauthorized"}

        stmt = select(models.User).where(models.User.id == UUID(student_id))
        result = await self.db.execute(stmt)
        user = result.scalars().first()

        if not user:
            return {"error": "Student not found"}

        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
        }

    async def get_student_requests(
        self, student_id: str, status: Optional[str] = None
    ) -> dict[str, Any]:
        """Get all service requests for a student."""
        if student_id != self.current_user_id:
            return {"error": "Unauthorized"}

        try:
            requests = await list_requests(self.db, student_id=student_id, status=status)
            return {
                "count": len(requests),
                "requests": [
                    {
                        "id": str(req.id),
                        "request_type": req.request_type,
                        "title": req.title,
                        "status": req.status,
                        "created_at": req.created_at.isoformat(),
                    }
                    for req in requests
                ],
            }
        except Exception as e:
            return {"error": f"Failed to retrieve requests: {str(e)}"}

    async def get_request_details(self, request_id: str) -> dict[str, Any]:
        """Get detailed information about a specific request."""
        try:
            req = await get_request(self.db, UUID(request_id))
            if not req:
                return {"error": "Request not found"}

            # Authorization: student can only see their own requests
            if req.student_id != self.current_user_id:
                return {"error": "Unauthorized"}

            return {
                "id": str(req.id),
                "student_id": req.student_id,
                "request_type": req.request_type,
                "title": req.title,
                "description": req.description,
                "status": req.status,
                "priority": req.priority,
                "department_id": req.department_id,
                "assigned_to": req.assigned_to,
                "created_at": req.created_at.isoformat(),
                "updated_at": req.updated_at.isoformat(),
            }
        except ValueError:
            return {"error": "Invalid request ID format"}
        except Exception as e:
            return {"error": f"Failed to retrieve request: {str(e)}"}

    async def create_service_request(
        self,
        student_id: str,
        request_type: str,
        title: str,
        description: Optional[str] = None,
        priority: str = "normal",
    ) -> dict[str, Any]:
        """Create a new service request."""
        if student_id != self.current_user_id:
            return {"error": "Unauthorized"}

        try:
            payload = ServiceRequestCreate(
                student_id=student_id,
                request_type=request_type,
                title=title,
                description=description,
                priority=priority,
            )
            req = await create_request(self.db, payload)
            return {
                "success": True,
                "request_id": str(req.id),
                "status": req.status,
                "created_at": req.created_at.isoformat(),
            }
        except Exception as e:
            return {"error": f"Failed to create request: {str(e)}"}

    # ========================================================================
    # FINANCE TOOLS
    # ========================================================================

    async def get_fee_balance(self, student_id: str) -> dict[str, Any]:
        """Get student's outstanding fee balance."""
        if student_id != self.current_user_id:
            return {"error": "Unauthorized"}

        try:
            # Get all unpaid invoices
            stmt = select(func.sum(models.Invoice.amount)).where(
                and_(
                    models.Invoice.student_id == student_id,
                    models.Invoice.paid == False,
                )
            )
            result = await self.db.execute(stmt)
            outstanding = result.scalars().first() or Decimal("0.00")

            # Get due dates
            stmt = select(models.Invoice.due_date).where(
                and_(
                    models.Invoice.student_id == student_id,
                    models.Invoice.paid == False,
                )
            ).order_by(models.Invoice.due_date)
            result = await self.db.execute(stmt)
            due_dates = result.scalars().all()

            next_due = due_dates[0].isoformat() if due_dates else None

            return {
                "student_id": student_id,
                "outstanding_balance": float(outstanding),
                "next_due_date": next_due,
                "currency": "USD",
            }
        except Exception as e:
            return {"error": f"Failed to retrieve fee balance: {str(e)}"}

    async def get_payment_status(self, student_id: str) -> dict[str, Any]:
        """Get status of recent payments."""
        if student_id != self.current_user_id:
            return {"error": "Unauthorized"}

        try:
            stmt = (
                select(models.Payment)
                .where(models.Payment.student_id == student_id)
                .order_by(models.Payment.created_at.desc())
                .limit(10)
            )
            result = await self.db.execute(stmt)
            payments = result.scalars().all()

            return {
                "recent_payments": [
                    {
                        "id": str(p.id),
                        "amount": float(p.amount),
                        "status": p.status,
                        "method": p.payment_method,
                        "created_at": p.created_at.isoformat(),
                        "confirmed_at": p.confirmed_at.isoformat() if p.confirmed_at else None,
                    }
                    for p in payments
                ],
            }
        except Exception as e:
            return {"error": f"Failed to retrieve payment status: {str(e)}"}

    async def get_invoice_details(self, student_id: str) -> dict[str, Any]:
        """Get details of unpaid invoices."""
        if student_id != self.current_user_id:
            return {"error": "Unauthorized"}

        try:
            stmt = (
                select(models.Invoice)
                .where(
                    and_(
                        models.Invoice.student_id == student_id,
                        models.Invoice.paid == False,
                    )
                )
                .order_by(models.Invoice.due_date)
            )
            result = await self.db.execute(stmt)
            invoices = result.scalars().all()

            return {
                "unpaid_invoices": [
                    {
                        "id": str(inv.id),
                        "amount": float(inv.amount),
                        "description": inv.description,
                        "due_date": inv.due_date.isoformat(),
                        "issued_date": inv.issued_date.isoformat(),
                        "days_until_due": (inv.due_date - datetime.datetime.utcnow()).days,
                    }
                    for inv in invoices
                ],
            }
        except Exception as e:
            return {"error": f"Failed to retrieve invoices: {str(e)}"}

    # ========================================================================
    # ENROLLMENT TOOLS
    # ========================================================================

    async def check_course_eligibility(
        self, student_id: str, course_code: str
    ) -> dict[str, Any]:
        """Check if student is eligible for a course."""
        if student_id != self.current_user_id:
            return {"error": "Unauthorized"}

        try:
            # Get course
            stmt = select(models.Course).where(models.Course.code == course_code)
            result = await self.db.execute(stmt)
            course = result.scalars().first()

            if not course:
                return {"eligible": False, "reason": "Course not found"}

            # Check capacity
            if course.enrolled_count >= course.capacity:
                return {"eligible": False, "reason": "Course is full"}

            # Check if already enrolled
            stmt = select(models.Enrollment).where(
                and_(
                    models.Enrollment.student_id == student_id,
                    models.Enrollment.course_id == course.id,
                )
            )
            result = await self.db.execute(stmt)
            existing = result.scalars().first()

            if existing:
                return {"eligible": False, "reason": "Already enrolled in this course"}

            # Check prerequisites
            stmt = select(models.Prerequisite).where(
                models.Prerequisite.course_id == course.id
            )
            result = await self.db.execute(stmt)
            prerequisites = result.scalars().all()

            missing_prerequisites = []
            for prereq in prerequisites:
                stmt = select(models.Enrollment).where(
                    and_(
                        models.Enrollment.student_id == student_id,
                        models.Enrollment.course_id == prereq.prerequisite_course_id,
                        models.Enrollment.status == "COMPLETED",
                    )
                )
                result = await self.db.execute(stmt)
                completed = result.scalars().first()

                if not completed:
                    missing_prerequisites.append(f"Prerequisite not completed")

            if missing_prerequisites:
                return {
                    "eligible": False,
                    "reason": "Missing prerequisites",
                    "missing": missing_prerequisites,
                }

            return {
                "eligible": True,
                "course_code": course_code,
                "course_title": course.title,
                "credits": course.credits,
            }
        except Exception as e:
            return {"error": f"Failed to check eligibility: {str(e)}"}

    async def get_course_details(self, course_code: str) -> dict[str, Any]:
        """Get details about a course."""
        try:
            stmt = select(models.Course).where(models.Course.code == course_code)
            result = await self.db.execute(stmt)
            course = result.scalars().first()

            if not course:
                return {"error": "Course not found"}

            # Get prerequisites
            stmt = select(models.Prerequisite).where(
                models.Prerequisite.course_id == course.id
            )
            result = await self.db.execute(stmt)
            prereqs = result.scalars().all()

            return {
                "code": course.code,
                "title": course.title,
                "credits": course.credits,
                "capacity": course.capacity,
                "enrolled": course.enrolled_count,
                "available_seats": course.capacity - course.enrolled_count,
                "description": course.description,
                "prerequisites_count": len(prereqs),
            }
        except Exception as e:
            return {"error": f"Failed to retrieve course details: {str(e)}"}

    async def get_enrollment_status(self, student_id: str) -> dict[str, Any]:
        """Get student's enrollment status and courses."""
        if student_id != self.current_user_id:
            return {"error": "Unauthorized"}

        try:
            stmt = (
                select(models.Enrollment)
                .where(models.Enrollment.student_id == student_id)
            )
            result = await self.db.execute(stmt)
            enrollments = result.scalars().all()

            active_courses = [e for e in enrollments if e.status == "ACTIVE"]
            completed_courses = [e for e in enrollments if e.status == "COMPLETED"]

            return {
                "active_courses": len(active_courses),
                "completed_courses": len(completed_courses),
                "current_credits": sum(
                    [
                        # Would need to join Course table to get credits
                        # For now, return placeholder
                        0
                    ]
                ),
            }
        except Exception as e:
            return {"error": f"Failed to retrieve enrollment status: {str(e)}"}

    # ========================================================================
    # DOCUMENT TOOLS
    # ========================================================================

    async def validate_document(
        self, document_id: str, document_type: str
    ) -> dict[str, Any]:
        """Validate an uploaded document."""
        try:
            stmt = select(models.Document).where(models.Document.id == UUID(document_id))
            result = await self.db.execute(stmt)
            document = result.scalars().first()

            if not document:
                return {"error": "Document not found"}

            # Validate document type matches
            if document.document_type.lower() != document_type.lower():
                return {
                    "valid": False,
                    "reason": f"Document type mismatch. Found {document.document_type}",
                }

            # In production, would perform OCR and field extraction here
            return {
                "valid": True,
                "document_type": document.document_type,
                "status": document.status,
                "verified_at": document.verified_at.isoformat() if document.verified_at else None,
            }
        except Exception as e:
            return {"error": f"Failed to validate document: {str(e)}"}

    async def get_document_status(self, student_id: str) -> dict[str, Any]:
        """Get verification status of documents."""
        if student_id != self.current_user_id:
            return {"error": "Unauthorized"}

        try:
            stmt = select(models.Document).where(
                models.Document.student_id == student_id
            )
            result = await self.db.execute(stmt)
            documents = result.scalars().all()

            verified = [d for d in documents if d.status == "VERIFIED"]
            pending = [d for d in documents if d.status == "PENDING"]
            rejected = [d for d in documents if d.status == "REJECTED"]

            return {
                "verified_documents": len(verified),
                "pending_documents": len(pending),
                "rejected_documents": len(rejected),
                "documents": [
                    {
                        "id": str(d.id),
                        "type": d.document_type,
                        "status": d.status,
                        "rejection_reason": d.rejection_reason,
                    }
                    for d in documents
                ],
            }
        except Exception as e:
            return {"error": f"Failed to retrieve document status: {str(e)}"}

    # ========================================================================
    # SUPPORT TOOLS
    # ========================================================================

    async def create_support_ticket(
        self,
        student_id: str,
        category: str,
        title: str,
        description: str,
        priority: str = "NORMAL",
    ) -> dict[str, Any]:
        """Create a support/complaint ticket."""
        if student_id != self.current_user_id:
            return {"error": "Unauthorized"}

        try:
            new_issue = models.Issue(
                student_id=student_id,
                category=category,
                title=title,
                description=description,
                priority=priority,
            )
            self.db.add(new_issue)
            await self.db.commit()

            return {
                "success": True,
                "ticket_id": str(new_issue.id),
                "status": new_issue.status,
                "category": new_issue.category,
                "created_at": new_issue.created_at.isoformat(),
            }
        except Exception as e:
            await self.db.rollback()
            return {"error": f"Failed to create ticket: {str(e)}"}

    async def get_issue_status(self, student_id: str) -> dict[str, Any]:
        """Get status of support issues."""
        if student_id != self.current_user_id:
            return {"error": "Unauthorized"}

        try:
            stmt = select(models.Issue).where(
                models.Issue.student_id == student_id
            )
            result = await self.db.execute(stmt)
            issues = result.scalars().all()

            open_issues = [i for i in issues if i.status == "OPEN"]
            in_progress = [i for i in issues if i.status == "IN_PROGRESS"]
            resolved = [i for i in issues if i.status == "RESOLVED"]

            return {
                "open_issues": len(open_issues),
                "in_progress": len(in_progress),
                "resolved_issues": len(resolved),
                "recent_issues": [
                    {
                        "id": str(i.id),
                        "title": i.title,
                        "category": i.category,
                        "status": i.status,
                        "priority": i.priority,
                        "created_at": i.created_at.isoformat(),
                    }
                    for i in sorted(issues, key=lambda x: x.created_at, reverse=True)[:5]
                ],
            }
        except Exception as e:
            return {"error": f"Failed to retrieve issue status: {str(e)}"}

    # ========================================================================
    # POLICY TOOLS
    # ========================================================================

    async def search_policies(self, query: str) -> dict[str, Any]:
        """Search university policies."""
        try:
            # Simple keyword search (could be enhanced with full-text search)
            query_lower = query.lower()
            stmt = select(models.PolicyDocument).where(
                or_(
                    models.PolicyDocument.title.ilike(f"%{query}%"),
                    models.PolicyDocument.content.ilike(f"%{query}%"),
                    models.PolicyDocument.category.ilike(f"%{query}%"),
                )
            )
            result = await self.db.execute(stmt)
            policies = result.scalars().all()

            return {
                "count": len(policies),
                "policies": [
                    {
                        "id": str(p.id),
                        "title": p.title,
                        "category": p.category,
                        "version": p.version,
                        "effective_date": p.effective_date.isoformat(),
                    }
                    for p in policies
                ],
            }
        except Exception as e:
            return {"error": f"Failed to search policies: {str(e)}"}

    async def get_policy_details(self, policy_id: str) -> dict[str, Any]:
        """Get full text of a policy."""
        try:
            stmt = select(models.PolicyDocument).where(
                models.PolicyDocument.id == UUID(policy_id)
            )
            result = await self.db.execute(stmt)
            policy = result.scalars().first()

            if not policy:
                return {"error": "Policy not found"}

            return {
                "id": str(policy.id),
                "title": policy.title,
                "content": policy.content,
                "category": policy.category,
                "version": policy.version,
                "effective_date": policy.effective_date.isoformat(),
                "updated_at": policy.updated_at.isoformat(),
            }
        except Exception as e:
            return {"error": f"Failed to retrieve policy: {str(e)}"}

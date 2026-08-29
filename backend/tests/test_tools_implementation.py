"""
Tests for all tool implementations

This file tests:
- Finance tools (fee balance, payments, invoices)
- Enrollment tools (course eligibility, details, status)
- Document tools (validation, status)
- Support tools (create ticket, get status)
- Policy tools (search, details)
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from backend.app.db.session import Base
from backend.app.db.models import (
    Invoice,
    Payment,
    Course,
    Enrollment,
    Document,
    Issue,
    PolicyDocument,
)
from backend.app.agents.tools import AgentTools


async def setup_test_db():
    """Create in-memory database for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session, engine


class TestFinanceTools:
    """Test finance agent tools."""

    @pytest.mark.asyncio
    async def test_get_fee_balance(self):
        """Test retrieving student fee balance."""
        async_session, engine = await setup_test_db()
        
        async with async_session() as db:
            student_id = str(uuid4())
            tools = AgentTools(db, student_id)

            # Create test invoices
            inv1 = Invoice(
                id=uuid4(),
                student_id=student_id,
                amount=Decimal("500.00"),
                due_date=datetime.utcnow() + timedelta(days=30),
                paid=False,
            )
            inv2 = Invoice(
                id=uuid4(),
                student_id=student_id,
                amount=Decimal("150.00"),
                due_date=datetime.utcnow() + timedelta(days=45),
                paid=False,
            )
            db.add(inv1)
            db.add(inv2)
            await db.commit()

            # Test get_fee_balance
            result = await tools.get_fee_balance(student_id)

            assert result["outstanding_balance"] == 650.0
            assert result["currency"] == "USD"
            assert result["next_due_date"] is not None

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_get_payment_status(self):
        """Test retrieving payment status."""
        async_session, engine = await setup_test_db()
        
        async with async_session() as db:
            student_id = str(uuid4())
            tools = AgentTools(db, student_id)

            # Create test payment
            payment = Payment(
                id=uuid4(),
                student_id=student_id,
                amount=Decimal("500.00"),
                status="CONFIRMED",
                payment_method="CREDIT_CARD",
            )
            db.add(payment)
            await db.commit()

            # Test get_payment_status
            result = await tools.get_payment_status(student_id)

            assert "recent_payments" in result
            assert len(result["recent_payments"]) == 1
            assert result["recent_payments"][0]["status"] == "CONFIRMED"

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_get_invoice_details(self):
        """Test retrieving invoice details."""
        async_session, engine = await setup_test_db()
        
        async with async_session() as db:
            student_id = str(uuid4())
            tools = AgentTools(db, student_id)

            # Create test invoice
            invoice = Invoice(
                id=uuid4(),
                student_id=student_id,
                amount=Decimal("750.00"),
                description="Semester Tuition",
                due_date=datetime.utcnow() + timedelta(days=15),
                paid=False,
            )
            db.add(invoice)
            await db.commit()

            # Test get_invoice_details
            result = await tools.get_invoice_details(student_id)

            assert "unpaid_invoices" in result
            assert len(result["unpaid_invoices"]) == 1
            assert result["unpaid_invoices"][0]["amount"] == 750.0
            assert result["unpaid_invoices"][0]["description"] == "Semester Tuition"

        await engine.dispose()


class TestEnrollmentTools:
    """Test enrollment agent tools."""

    @pytest.mark.asyncio
    async def test_get_course_details(self):
        """Test retrieving course details."""
        async_session, engine = await setup_test_db()
        
        async with async_session() as db:
            tools = AgentTools(db, str(uuid4()))

            # Create test course
            course = Course(
                id=uuid4(),
                code="CS101",
                title="Intro to CS",
                credits=3,
                capacity=30,
                enrolled_count=25,
            )
            db.add(course)
            await db.commit()

            # Test get_course_details
            result = await tools.get_course_details("CS101")

            assert result["code"] == "CS101"
            assert result["title"] == "Intro to CS"
            assert result["credits"] == 3
            assert result["capacity"] == 30
            assert result["enrolled"] == 25
            assert result["available_seats"] == 5

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_check_course_eligibility_not_found(self):
        """Test course eligibility check when course not found."""
        async_session, engine = await setup_test_db()
        
        async with async_session() as db:
            student_id = str(uuid4())
            tools = AgentTools(db, student_id)

            # Test with non-existent course
            result = await tools.check_course_eligibility(student_id, "FAKE101")

            assert result["eligible"] is False
            assert "not found" in result["reason"].lower()

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_get_enrollment_status(self):
        """Test retrieving student enrollment status."""
        async_session, engine = await setup_test_db()
        
        async with async_session() as db:
            student_id = str(uuid4())
            tools = AgentTools(db, student_id)

            # Create test course and enrollment
            course = Course(
                id=uuid4(),
                code="CS101",
                title="Intro to CS",
                credits=3,
                capacity=30,
                enrolled_count=20,
            )
            db.add(course)
            await db.commit()

            enrollment = Enrollment(
                id=uuid4(),
                student_id=student_id,
                course_id=course.id,
                status="ACTIVE",
            )
            db.add(enrollment)
            await db.commit()

            # Test get_enrollment_status
            result = await tools.get_enrollment_status(student_id)

            assert result["active_courses"] == 1
            assert result["completed_courses"] == 0

        await engine.dispose()


class TestDocumentTools:
    """Test document agent tools."""

    @pytest.mark.asyncio
    async def test_get_document_status(self):
        """Test retrieving document status."""
        async_session, engine = await setup_test_db()
        
        async with async_session() as db:
            student_id = str(uuid4())
            tools = AgentTools(db, student_id)

            # Create test documents
            doc_verified = Document(
                id=uuid4(),
                student_id=student_id,
                document_type="DEGREE",
                file_name="degree.pdf",
                file_path="/path/degree.pdf",
                status="VERIFIED",
            )
            doc_pending = Document(
                id=uuid4(),
                student_id=student_id,
                document_type="CNIC",
                file_name="cnic.pdf",
                file_path="/path/cnic.pdf",
                status="PENDING",
            )
            db.add(doc_verified)
            db.add(doc_pending)
            await db.commit()

            # Test get_document_status
            result = await tools.get_document_status(student_id)

            assert result["verified_documents"] == 1
            assert result["pending_documents"] == 1
            assert result["rejected_documents"] == 0
            assert len(result["documents"]) == 2

        await engine.dispose()


class TestSupportTools:
    """Test support agent tools."""

    @pytest.mark.asyncio
    async def test_create_support_ticket(self):
        """Test creating a support ticket."""
        async_session, engine = await setup_test_db()
        
        async with async_session() as db:
            student_id = str(uuid4())
            tools = AgentTools(db, student_id)

            # Test create_support_ticket
            result = await tools.create_support_ticket(
                student_id=student_id,
                category="IT",
                title="Cannot login",
                description="Getting 403 error",
                priority="HIGH",
            )

            assert result["success"] is True
            assert result["status"] == "OPEN"
            assert result["category"] == "IT"

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_get_issue_status(self):
        """Test retrieving issue status."""
        async_session, engine = await setup_test_db()
        
        async with async_session() as db:
            student_id = str(uuid4())
            tools = AgentTools(db, student_id)

            # Create test issues
            issue_open = Issue(
                id=uuid4(),
                student_id=student_id,
                category="IT",
                title="Network issue",
                description="WiFi not working",
                priority="HIGH",
                status="OPEN",
            )
            issue_resolved = Issue(
                id=uuid4(),
                student_id=student_id,
                category="FACILITIES",
                title="Broken projector",
                description="Fixed",
                priority="NORMAL",
                status="RESOLVED",
                resolved_at=datetime.utcnow(),
            )
            db.add(issue_open)
            db.add(issue_resolved)
            await db.commit()

            # Test get_issue_status
            result = await tools.get_issue_status(student_id)

            assert result["open_issues"] == 1
            assert result["resolved_issues"] == 1

        await engine.dispose()


class TestPolicyTools:
    """Test policy agent tools."""

    @pytest.mark.asyncio
    async def test_search_policies(self):
        """Test policy search."""
        async_session, engine = await setup_test_db()
        
        async with async_session() as db:
            tools = AgentTools(db, str(uuid4()))

            # Create test policies
            policy1 = PolicyDocument(
                id=uuid4(),
                title="Attendance Policy",
                content="Students must attend 75% of classes",
                category="ACADEMIC",
                version="1.0",
                effective_date=datetime.utcnow(),
            )
            policy2 = PolicyDocument(
                id=uuid4(),
                title="Academic Integrity",
                content="No plagiarism or cheating",
                category="CONDUCT",
                version="1.0",
                effective_date=datetime.utcnow(),
            )
            db.add(policy1)
            db.add(policy2)
            await db.commit()

            # Test search_policies
            result = await tools.search_policies("attendance")

            assert result["count"] == 1
            assert result["policies"][0]["title"] == "Attendance Policy"

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_get_policy_details(self):
        """Test retrieving policy details."""
        async_session, engine = await setup_test_db()
        
        async with async_session() as db:
            tools = AgentTools(db, str(uuid4()))

            # Create test policy
            policy = PolicyDocument(
                id=uuid4(),
                title="Attendance Policy",
                content="Students must attend 75% of classes",
                category="ACADEMIC",
                version="1.0",
                effective_date=datetime.utcnow(),
            )
            db.add(policy)
            await db.commit()

            # Test get_policy_details
            result = await tools.get_policy_details(str(policy.id))

            assert result["title"] == "Attendance Policy"
            assert "75%" in result["content"]

        await engine.dispose()


class TestAuthorizationEnforcement:
    """Test that authorization is enforced in tools."""

    @pytest.mark.asyncio
    async def test_unauthorized_fee_balance_access(self):
        """Test that students cannot access other students' fee balance."""
        async_session, engine = await setup_test_db()
        
        async with async_session() as db:
            student_id = str(uuid4())
            other_student = str(uuid4())
            tools = AgentTools(db, student_id)

            # Try to access other student's fee balance
            result = await tools.get_fee_balance(other_student)

            assert "error" in result

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_unauthorized_document_status_access(self):
        """Test that students cannot access other students' documents."""
        async_session, engine = await setup_test_db()
        
        async with async_session() as db:
            student_id = str(uuid4())
            other_student = str(uuid4())
            tools = AgentTools(db, student_id)

            # Try to access other student's documents
            result = await tools.get_document_status(other_student)

            assert "error" in result

        await engine.dispose()

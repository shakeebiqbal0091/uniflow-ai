"""
Seed data for testing tools

This script creates sample data for the new models:
- Invoices
- Payments  
- Courses
- Documents
- Issues
- Policy Documents
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from backend.app.db.models import (
    Invoice,
    Payment,
    Course,
    Enrollment,
    Prerequisite,
    Document,
    Issue,
    PolicyDocument,
)
from backend.app.db.session import AsyncSessionLocal


async def seed_data():
    """Create seed data for testing."""
    async with AsyncSessionLocal() as db:
        # Create sample courses
        course_db = Course(
            id=uuid4(),
            code="CS101",
            title="Introduction to Computer Science",
            credits=3,
            capacity=30,
            enrolled_count=25,
            description="Fundamental concepts of computer science",
        )
        course_algorithms = Course(
            id=uuid4(),
            code="CS201",
            title="Algorithms and Data Structures",
            credits=4,
            capacity=25,
            enrolled_count=20,
            description="Advanced algorithms and data structures",
        )
        db.add(course_db)
        db.add(course_algorithms)

        # Create prerequisite relationship
        prereq = Prerequisite(
            id=uuid4(),
            course_id=course_algorithms.id,
            prerequisite_course_id=course_db.id,
            minimum_grade="C",
        )
        db.add(prereq)

        # Create sample invoices (unpaid)
        invoice1 = Invoice(
            id=uuid4(),
            student_id="test-student",
            amount=Decimal("500.00"),
            description="Spring 2026 Tuition",
            due_date=datetime.utcnow() + timedelta(days=30),
            issued_date=datetime.utcnow() - timedelta(days=10),
            paid=False,
        )
        invoice2 = Invoice(
            id=uuid4(),
            student_id="test-student",
            amount=Decimal("150.00"),
            description="Lab Fee",
            due_date=datetime.utcnow() + timedelta(days=45),
            issued_date=datetime.utcnow() - timedelta(days=5),
            paid=False,
        )
        db.add(invoice1)
        db.add(invoice2)

        # Create sample payment
        payment = Payment(
            id=uuid4(),
            student_id="test-student",
            invoice_id=invoice1.id,
            amount=Decimal("500.00"),
            payment_method="CREDIT_CARD",
            status="PENDING",
            transaction_id="TXN-001",
        )
        db.add(payment)

        # Create sample documents
        doc1 = Document(
            id=uuid4(),
            student_id="test-student",
            document_type="DEGREE",
            file_name="bachelor_degree.pdf",
            file_path="/documents/test-student/degree.pdf",
            status="VERIFIED",
            verified_at=datetime.utcnow() - timedelta(days=7),
            verified_by="admin-001",
        )
        doc2 = Document(
            id=uuid4(),
            student_id="test-student",
            document_type="CNIC",
            file_name="cnic_scan.pdf",
            file_path="/documents/test-student/cnic.pdf",
            status="PENDING",
        )
        db.add(doc1)
        db.add(doc2)

        # Create sample issues
        issue1 = Issue(
            id=uuid4(),
            student_id="test-student",
            category="IT",
            title="Cannot access online portal",
            description="Getting 403 error when trying to login to the student portal",
            priority="HIGH",
            status="OPEN",
        )
        issue2 = Issue(
            id=uuid4(),
            student_id="test-student",
            category="FACILITIES",
            title="Broken projector in room 205",
            description="The projector in room 205 stopped working during class",
            priority="NORMAL",
            status="RESOLVED",
            resolved_at=datetime.utcnow() - timedelta(days=1),
        )
        db.add(issue1)
        db.add(issue2)

        # Create sample policies
        policy_attendance = PolicyDocument(
            id=uuid4(),
            title="Attendance Policy",
            content="""
            Attendance Policy 2026
            
            1. All students are required to attend at least 75% of classes
            2. Excused absences: Medical emergencies, university-approved events
            3. Unexcused absence: Will result in grade penalty
            4. Three late arrivals equal one absence
            5. Professor discretion for extenuating circumstances
            """,
            category="ACADEMIC",
            version="2.0",
            effective_date=datetime.utcnow() - timedelta(days=90),
        )
        policy_academic = PolicyDocument(
            id=uuid4(),
            title="Academic Integrity Policy",
            content="""
            Academic Integrity Policy 2026
            
            Students are expected to:
            1. Complete their own work
            2. Cite all sources properly
            3. Not plagiarize or cheat
            4. Report academic misconduct
            
            Violations may result in:
            - Grade penalty
            - Course failure
            - Suspension
            - Expulsion
            """,
            category="ACADEMIC",
            version="1.5",
            effective_date=datetime.utcnow() - timedelta(days=180),
        )
        db.add(policy_attendance)
        db.add(policy_academic)

        await db.commit()
        print("✓ Seed data created successfully")
        print("  - 2 courses created")
        print("  - 1 prerequisite relationship created")
        print("  - 2 invoices created (unpaid)")
        print("  - 1 payment created (pending)")
        print("  - 2 documents created")
        print("  - 2 issues created")
        print("  - 2 policies created")


if __name__ == "__main__":
    asyncio.run(seed_data())

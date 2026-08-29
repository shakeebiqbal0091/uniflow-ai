import uuid
import datetime
from enum import Enum
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean, Numeric, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.app.db.session import Base


class RequestStatus(str, Enum):
    NEW = "NEW"
    CLASSIFYING = "CLASSIFYING"
    WAITING_FOR_INFORMATION = "WAITING_FOR_INFORMATION"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"
    APPROVED = "APPROVED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(String, index=True, nullable=False)
    request_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String, default="normal")
    status = Column(String, default=RequestStatus.NEW.value, nullable=False)
    department_id = Column(String, nullable=True)
    assigned_to = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    sla_due_at = Column(DateTime, nullable=True)
    source = Column(String, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="STUDENT")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("Student", back_populates="user", uselist=False)


class Student(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    student_number = Column(String, unique=True, index=True, nullable=False)
    program = Column(String, nullable=True)
    enrolled = Column(Boolean, default=True)

    user = relationship("User", back_populates="student")


# ============================================================================
# FINANCE MODELS
# ============================================================================


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(String, index=True, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(String, nullable=True)
    due_date = Column(DateTime, nullable=False)
    issued_date = Column(DateTime, default=datetime.datetime.utcnow)
    paid = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(String, index=True, nullable=False)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String, nullable=True)
    status = Column(String, default="PENDING")  # PENDING, CONFIRMED, FAILED
    transaction_id = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)


# ============================================================================
# ENROLLMENT MODELS
# ============================================================================


class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    credits = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False)
    enrolled_count = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(String, index=True, nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    status = Column(String, default="ACTIVE")  # ACTIVE, COMPLETED, WITHDRAWN
    grade = Column(String, nullable=True)
    enrolled_at = Column(DateTime, default=datetime.datetime.utcnow)


class Prerequisite(Base):
    __tablename__ = "prerequisites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    prerequisite_course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    minimum_grade = Column(String, default="D")


# ============================================================================
# DOCUMENT MODELS
# ============================================================================


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(String, index=True, nullable=False)
    document_type = Column(String, nullable=False)  # DEGREE, CNIC, TRANSCRIPT, etc
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(String, default="PENDING")  # PENDING, VERIFIED, REJECTED
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(String, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# ============================================================================
# SUPPORT MODELS
# ============================================================================


class Issue(Base):
    __tablename__ = "issues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(String, index=True, nullable=False)
    category = Column(String, nullable=False)  # IT, FACILITIES, ACADEMIC, etc
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String, default="NORMAL")  # LOW, NORMAL, HIGH, CRITICAL
    status = Column(String, default="OPEN")  # OPEN, IN_PROGRESS, RESOLVED, CLOSED
    assigned_to = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


# ============================================================================
# POLICY MODELS
# ============================================================================


class PolicyDocument(Base):
    __tablename__ = "policy_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String, index=True, nullable=False)  # ACADEMIC, FINANCIAL, CONDUCT, etc
    version = Column(String, default="1.0")
    effective_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

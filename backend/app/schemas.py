from pydantic import BaseModel, validator
from typing import Optional
from uuid import UUID
import datetime
from typing import Any

from backend.app.db.models import RequestStatus


class ServiceRequestCreate(BaseModel):
    student_id: Optional[str] = None
    request_type: str
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "normal"
    department_id: Optional[str] = None
    source: Optional[str] = None
    status: Optional[RequestStatus] = RequestStatus.NEW

    @validator("status")
    def validate_status(cls, value):
        if value is None:
            return RequestStatus.NEW
        return RequestStatus(value.value if isinstance(value, RequestStatus) else value.upper())


class ServiceRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[RequestStatus] = None
    department_id: Optional[str] = None
    assigned_to: Optional[str] = None

    @validator("status")
    def validate_status(cls, value):
        if value is None:
            return None
        return RequestStatus(value.value if isinstance(value, RequestStatus) else value.upper())


class ServiceRequestRead(BaseModel):
    id: UUID
    student_id: str
    request_type: str
    title: str
    description: Optional[str]
    priority: str
    status: str
    department_id: Optional[str]
    assigned_to: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    resolved_at: Optional[datetime.datetime]
    sla_due_at: Optional[datetime.datetime]
    source: Optional[str]

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


class UserRead(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str]
    is_active: bool
    role: str

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
    scopes: Optional[Any] = None

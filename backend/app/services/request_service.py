from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db import models
from backend.app.schemas import ServiceRequestCreate
from sqlalchemy import select, update
from typing import List, Optional
from uuid import UUID

VALID_REQUEST_STATUSES = {
    status.value for status in models.RequestStatus
}


def normalize_request_status(value: str | models.RequestStatus | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, models.RequestStatus):
        return value.value

    normalized = str(value).strip().upper()
    if normalized not in VALID_REQUEST_STATUSES:
        raise ValueError(f"Invalid request status: {value}")
    return normalized


async def create_request(db: AsyncSession, payload: ServiceRequestCreate):
    status_value = normalize_request_status(payload.status)
    req = models.ServiceRequest(
        student_id=payload.student_id,
        request_type=payload.request_type,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        department_id=payload.department_id,
        source=payload.source,
        status=status_value or models.RequestStatus.NEW.value,
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req


async def get_request(db: AsyncSession, request_id: UUID) -> Optional[models.ServiceRequest]:
    return await db.get(models.ServiceRequest, request_id)


async def list_requests(db: AsyncSession, student_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[models.ServiceRequest]:
    stmt = select(models.ServiceRequest).limit(limit).offset(offset)
    if student_id:
        stmt = stmt.where(models.ServiceRequest.student_id == student_id)
    if status:
        normalized_status = normalize_request_status(status)
        stmt = stmt.where(models.ServiceRequest.status == normalized_status)
    res = await db.execute(stmt)
    return res.scalars().all()


async def update_request(db: AsyncSession, request_id: UUID, fields: dict) -> Optional[models.ServiceRequest]:
    if "status" in fields:
        fields["status"] = normalize_request_status(fields["status"])
    stmt = update(models.ServiceRequest).where(models.ServiceRequest.id == request_id).values(**fields)
    await db.execute(stmt)
    await db.commit()
    return await get_request(db, request_id)

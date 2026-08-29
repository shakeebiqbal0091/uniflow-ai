from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import get_db
from backend.app.api.security import require_admin
from backend.app.db import models
from backend.app.schemas import ServiceRequestRead
from backend.app.services.request_service import list_requests, get_request, update_request

router = APIRouter()


class AssignRequestPayload(BaseModel):
    assigned_to: Optional[str] = None
    department_id: Optional[str] = None


class RequestStatusPayload(BaseModel):
    status: str


@router.get("/requests", response_model=list[ServiceRequestRead])
async def list_admin_requests(
    status: str | None = Query(None),
    department_id: str | None = Query(None),
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    items = await list_requests(db, status=status, limit=limit, offset=offset)
    if department_id:
        items = [item for item in items if item.department_id == department_id]
    return items


@router.patch("/requests/{request_id}/assign", response_model=ServiceRequestRead)
async def assign_request(
    request_id: UUID,
    payload: AssignRequestPayload,
    db: AsyncSession = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    req = await get_request(db, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    fields = {}
    if payload.assigned_to is not None:
        fields["assigned_to"] = payload.assigned_to
    if payload.department_id is not None:
        fields["department_id"] = payload.department_id
    if not fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No assignment fields provided")

    updated = await update_request(db, request_id, fields)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return updated


@router.patch("/requests/{request_id}/status", response_model=ServiceRequestRead)
async def update_request_status(
    request_id: UUID,
    payload: RequestStatusPayload,
    db: AsyncSession = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    try:
        updated = await update_request(db, request_id, {"status": payload.status})
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return updated

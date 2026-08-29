from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.schemas import ServiceRequestCreate, ServiceRequestRead, ServiceRequestUpdate
from backend.app.api.dependencies import get_db
from backend.app.services.request_service import create_request, get_request, list_requests, update_request
from backend.app.api.security import get_current_user, require_owner_or_admin, get_user_identifier
from backend.app.db import models
from uuid import UUID

router = APIRouter()


@router.post("/", response_model=ServiceRequestRead, status_code=status.HTTP_201_CREATED)
async def create_new_request(payload: ServiceRequestCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    data = payload.dict(exclude_unset=True)
    role = getattr(current_user, 'role', None)
    if not (role and role in ("SUPER_ADMIN", "ADMIN")):
        data['student_id'] = get_user_identifier(current_user)
    if 'status' not in data:
        data['status'] = "NEW"
    try:
        req = await create_request(db, ServiceRequestCreate(**data))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return req


@router.get("/{request_id}", response_model=ServiceRequestRead)
async def read_request(request: models.ServiceRequest = Depends(require_owner_or_admin)):
    return request


@router.get("/", response_model=list[ServiceRequestRead])
async def read_requests(student_id: str | None = Query(None), status: str | None = Query(None), limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    role = getattr(current_user, 'role', None)
    if not (role and role in ("SUPER_ADMIN", "ADMIN")):
        student_id = get_user_identifier(current_user)

    items = await list_requests(db, student_id=student_id, status=status, limit=limit, offset=offset)
    return items


@router.patch("/{request_id}", response_model=ServiceRequestRead)
async def patch_request(request_id: UUID, payload: ServiceRequestUpdate, db: AsyncSession = Depends(get_db), _auth=Depends(require_owner_or_admin)):
    fields = {k: v for k, v in payload.dict(exclude_unset=True).items()}
    if not fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    try:
        updated = await update_request(db, request_id, fields)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return updated

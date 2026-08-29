from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.auth_service import decode_token, get_user_by_email
from backend.app.api.dependencies import get_db
from uuid import UUID
from backend.app.db import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_user_identifier(current_user) -> str:
    return str(getattr(current_user, "id", ""))


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(token)
        email: str = payload.get("sub") or payload.get("email")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    user = await get_user_by_email(db, email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def require_owner_or_admin(request_id: UUID, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> models.ServiceRequest:
    role = getattr(current_user, "role", None)
    req = await db.get(models.ServiceRequest, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if role and role in ("SUPER_ADMIN", "ADMIN"):
        return req

    user_identifier = get_user_identifier(current_user)
    if req.student_id != user_identifier:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this request")
    return req


async def require_admin(current_user=Depends(get_current_user)) -> models.User:
    role = getattr(current_user, "role", None)
    if role not in ("SUPER_ADMIN", "ADMIN"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user

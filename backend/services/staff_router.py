"""
staff_router.py
───────────────
Admin-only staff management: list, create, and update (role / active /
password) clinic user accounts. Router-level require_role guard is
defense-in-depth on top of the RBAC middleware.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from models import SessionLocal, User
from security import ALL_ROLES, hash_password, require_role

staff_router = APIRouter(dependencies=[Depends(require_role("admin"))])


class CreateStaffRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    full_name: str = ""
    password: str = Field(min_length=6)
    role: str


class UpdateStaffRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=6)


def _staff_payload(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _validate_role(role: str) -> None:
    if role not in ALL_ROLES:
        raise HTTPException(status_code=422, detail=f"Role must be one of {list(ALL_ROLES)}")


def _other_active_admins(db, user_id: str) -> int:
    return (
        db.query(User)
        .filter(User.role == "admin", User.is_active == True, User.id != user_id)  # noqa: E712
        .count()
    )


@staff_router.get("", tags=["Staff"])
async def list_staff():
    with SessionLocal() as db:
        users = db.query(User).order_by(User.created_at).all()
        return {"users": [_staff_payload(u) for u in users]}


@staff_router.post("", tags=["Staff"])
async def create_staff(body: CreateStaffRequest):
    _validate_role(body.role)
    username = body.username.strip().lower()
    with SessionLocal() as db:
        if db.query(User).filter(User.username == username).first():
            raise HTTPException(status_code=409, detail="Username already exists")
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            full_name=body.full_name.strip(),
            password_hash=hash_password(body.password),
            role=body.role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"user": _staff_payload(user)}


@staff_router.patch("/{user_id}", tags=["Staff"])
async def update_staff(
    user_id: str,
    body: UpdateStaffRequest,
    current: User = Depends(require_role("admin")),
):
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        if body.is_active is False and user.id == current.id:
            raise HTTPException(status_code=400, detail="You cannot deactivate your own account")

        demoting = body.role is not None and body.role != "admin" and user.role == "admin"
        deactivating = body.is_active is False
        if (demoting or deactivating) and user.role == "admin":
            if _other_active_admins(db, user.id) == 0:
                raise HTTPException(status_code=400, detail="Cannot remove the last active admin")

        if body.role is not None:
            _validate_role(body.role)
            if body.role != "admin" and user.id == current.id:
                raise HTTPException(status_code=400, detail="You cannot demote your own account")
            user.role = body.role
        if body.is_active is not None:
            user.is_active = body.is_active
        if body.password:
            user.password_hash = hash_password(body.password)

        db.commit()
        db.refresh(user)
        return {"user": _staff_payload(user)}

"""
auth_router.py
──────────────
Login / logout / current-user endpoints. The JWT is delivered in an
httpOnly cookie so the browser never exposes it to JS; the Next.js
middleware verifies the same token for page routing.
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from config import AUTH_COOKIE_NAME
from models import SessionLocal, User
from security import (
    ACCESS_TOKEN_EXPIRE_HOURS,
    COOKIE_SECURE,
    create_access_token,
    get_current_user,
    verify_password,
)

auth_router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "name": user.full_name or user.username,
        "role": user.role,
    }


@auth_router.post("/login", tags=["Auth"])
async def login(body: LoginRequest, response: Response):
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == body.username.strip()).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is deactivated")

    token = create_access_token(user)
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        path="/",
    )
    return {"user": _user_payload(user)}


@auth_router.post("/logout", tags=["Auth"])
async def logout(response: Response):
    response.delete_cookie(AUTH_COOKIE_NAME, path="/")
    return {"ok": True}


@auth_router.get("/me", tags=["Auth"])
async def me(user: User = Depends(get_current_user)):
    return {"user": _user_payload(user)}

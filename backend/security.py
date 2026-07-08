"""
security.py
───────────
Authentication + role-based access control for the AYUSH backend.

- Password hashing (bcrypt) and JWT issue/verify (PyJWT, HS256).
- FastAPI dependencies: get_current_user / require_role(...) for routers
  that want explicit guards (auth + staff routers).
- RBACMiddleware: single enforcement point for the whole API surface.
  Routes are matched against an ordered rules table (first match wins),
  so the 40+ existing routes in main.py need no per-route changes.

The token travels in an httpOnly cookie (AUTH_COOKIE_NAME); server-to-server
callers may instead send `Authorization: Bearer <token>`.
"""
import os
import re
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config import AUTH_COOKIE_NAME, DEFAULT_ACCESS_TOKEN_EXPIRE_HOURS
from models import SessionLocal, User

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", str(DEFAULT_ACCESS_TOKEN_EXPIRE_HOURS))
)
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

RECEPTIONIST = "receptionist"
DOCTOR = "doctor"
ADMIN = "admin"
ALL_ROLES = (RECEPTIONIST, DOCTOR, ADMIN)


def _require_secret() -> str:
    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is not set. Add it to backend/.env (e.g. `openssl rand -hex 32`)."
        )
    return SECRET_KEY


# ── Passwords ──────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


# ── Tokens ─────────────────────────────────────────────────────────────────────

def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "username": user.username,
        "name": user.full_name or user.username,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, _require_secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Returns the claims dict, or raises HTTPException(401)."""
    try:
        return jwt.decode(token, _require_secret(), algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def _token_from_request(request: Request) -> str | None:
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if token:
        return token
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[len("Bearer "):]
    return None


def _load_user(user_id: str) -> User | None:
    with SessionLocal() as db:
        return db.get(User, user_id)


# ── Dependencies (explicit guards for auth/staff routers) ──────────────────────

def get_current_user(request: Request) -> User:
    token = _token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    claims = decode_token(token)
    user = _load_user(claims.get("sub", ""))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Account not found or deactivated")
    return user


def require_role(*roles: str):
    def dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return dep


# ── RBAC rules ─────────────────────────────────────────────────────────────────
# Paths open to unauthenticated clients (exact match).
PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/auth/login",
}

# Clinical-history sub-resources of /api/patients are doctor/admin only even
# though the directory itself is shared — matched before the prefix rules.
_PATIENT_CLINICAL_RE = re.compile(r"^/api/patients/[^/]+/(history|diagnoses)$")

# (method or None = any, path prefix, allowed roles) — checked in order,
# first match wins. Paths not matched by any rule require authentication
# but no specific role.
RBAC_RULES = [
    (None, "/api/auth/", ALL_ROLES),
    (None, "/api/staff", (ADMIN,)),
    # Doctor: clinical workflow
    ("GET", "/api/diagnoses/completed", (DOCTOR, ADMIN)),
    ("GET", "/api/consultations/", (DOCTOR, ADMIN)),  # /{visit_id}/treatment
    ("POST", "/api/consultations", ALL_ROLES),  # receptionist adds to queue too
    (None, "/api/visits/", (DOCTOR, ADMIN)),
    (None, "/api/recommend", (DOCTOR, ADMIN)),
    (None, "/api/prescribe", (DOCTOR, ADMIN)),
    (None, "/api/feedback", (DOCTOR, ADMIN)),
    (None, "/api/outcomes", (DOCTOR, ADMIN)),
    (None, "/api/diseases", (DOCTOR, ADMIN)),
    (None, "/api/dietary-plan", (DOCTOR, ADMIN)),
    (None, "/api/copilot/treatment", (DOCTOR, ADMIN)),
    (None, "/api/copilot/doctor", (DOCTOR, ADMIN)),
    (None, "/api/gemma4-turn", ALL_ROLES),
    (None, "/api/phi4-turn", (DOCTOR, ADMIN)),
    # Receptionist: intake
    ("POST", "/api/patients", (RECEPTIONIST, ADMIN)),
    (None, "/api/copilot/registration", (RECEPTIONIST, ADMIN)),
    (None, "/api/copilot/consultation", (RECEPTIONIST, ADMIN)),
    # Voice pipeline is used by both intake and treatment flows
    (None, "/api/bind-run-id", ALL_ROLES),
    (None, "/api/transcribe", ALL_ROLES),
    (None, "/api/translate", ALL_ROLES),
    # Shared patient directory (GET list/search/{id})
    ("GET", "/api/patients", ALL_ROLES),
    # Admin surfaces
    (None, "/api/analytics", (ADMIN,)),
    (None, "/api/forecast", (ADMIN,)),
    (None, "/api/trends", (ADMIN,)),
    (None, "/api/ml/", (ADMIN,)),
    (None, "/api/model/", (ADMIN,)),
    (None, "/api/admin", (ADMIN,)),
]


def _matches(path: str, prefix: str) -> bool:
    if prefix.endswith("/"):
        return path.startswith(prefix)
    return path == prefix or path.startswith(prefix + "/")


def roles_for(method: str, path: str):
    """Allowed roles for a request, or None if any authenticated user may pass."""
    if _PATIENT_CLINICAL_RE.match(path):
        return (DOCTOR, ADMIN)
    for rule_method, prefix, roles in RBAC_RULES:
        if rule_method is not None and rule_method != method:
            continue
        if _matches(path, prefix):
            return roles
    return None


class RBACMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if request.method == "OPTIONS" or path in PUBLIC_PATHS:
            return await call_next(request)

        token = _token_from_request(request)
        if not token:
            return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
        try:
            claims = decode_token(token)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

        user = _load_user(claims.get("sub", ""))
        if user is None or not user.is_active:
            return JSONResponse(
                status_code=401, content={"detail": "Account not found or deactivated"}
            )

        allowed = roles_for(request.method, path)
        if allowed is not None and user.role not in allowed:
            return JSONResponse(status_code=403, content={"detail": "Insufficient role"})

        request.state.user = user
        return await call_next(request)

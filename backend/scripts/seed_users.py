"""
seed_users.py
─────────────
Creates the `users` table (via init_db / create_all — additive, existing
tables untouched) and idempotently upserts one demo account per role.

Default credentials (override the passwords via env before running):
    admin / Admin@123          SEED_ADMIN_PASSWORD
    doctor / Doctor@123        SEED_DOCTOR_PASSWORD
    reception / Reception@123  SEED_RECEPTION_PASSWORD

Re-running updates the role/name/active flag of existing usernames but
never overwrites a password unless SEED_RESET_PASSWORDS=true.

Run from backend/:
    ./venv/bin/python3.11 scripts/seed_users.py
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import SessionLocal, User, init_db
from security import hash_password

SEED_USERS = [
    {
        "username": "admin",
        "full_name": "Administrator",
        "role": "admin",
        "password": os.getenv("SEED_ADMIN_PASSWORD", "Admin@123"),
    },
    {
        "username": "doctor",
        "full_name": "Dr. Demo",
        "role": "doctor",
        "password": os.getenv("SEED_DOCTOR_PASSWORD", "Doctor@123"),
    },
    {
        "username": "reception",
        "full_name": "Front Desk",
        "role": "receptionist",
        "password": os.getenv("SEED_RECEPTION_PASSWORD", "Reception@123"),
    },
]

RESET_PASSWORDS = os.getenv("SEED_RESET_PASSWORDS", "false").lower() == "true"


def seed() -> None:
    init_db()
    with SessionLocal() as db:
        for spec in SEED_USERS:
            user = db.query(User).filter(User.username == spec["username"]).first()
            if user is None:
                db.add(
                    User(
                        id=str(uuid.uuid4()),
                        username=spec["username"],
                        full_name=spec["full_name"],
                        password_hash=hash_password(spec["password"]),
                        role=spec["role"],
                        is_active=True,
                    )
                )
                print(f"✓ created {spec['username']} ({spec['role']}) — password: {spec['password']}")
            else:
                user.full_name = spec["full_name"]
                user.role = spec["role"]
                user.is_active = True
                if RESET_PASSWORDS:
                    user.password_hash = hash_password(spec["password"])
                print(f"• updated {spec['username']} ({spec['role']})"
                      + (" — password reset" if RESET_PASSWORDS else ""))
        db.commit()
    print("Done.")


if __name__ == "__main__":
    seed()

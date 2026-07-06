"""
setup_rbac.py
─────────────
One-shot, idempotent database setup for the RBAC/auth feature.
Safe to run multiple times; it only ever ADDs (tables, columns, indexes,
seed users) and never drops or rewrites existing data.

What it does, in order:
  1. Verifies DATABASE_URL connects and SECRET_KEY is set in backend/.env
  2. Backfills treatment_feedbacks columns   (same as migrate_revamp.py)
  3. Backfills medical_records indexes       (same as add_medical_record_indexes.py)
  4. Creates any missing tables via init_db() — this adds the new `users` table
  5. Seeds the demo accounts                 (same as seed_users.py)

Run from backend/:
    ./venv/bin/python3.11 scripts/setup_rbac.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from sqlalchemy import inspect, text

STEP = "\n─── {} " + "─" * 40


def main() -> None:
    # 1. Preconditions ─ fail fast with actionable messages
    print(STEP.format("1/5 Checking environment"))
    if not os.getenv("SECRET_KEY"):
        sys.exit(
            "✗ SECRET_KEY is missing from backend/.env\n"
            "  Generate one and add it:\n"
            "      echo \"SECRET_KEY=$(openssl rand -hex 32)\" >> .env\n"
            "  Then copy the SAME value into the frontend .env.local as JWT_SECRET.\n"
            "  (See RBAC_MIGRATION_GUIDE.md at the repo root.)"
        )
    from models import engine, init_db  # imports load .env and build the engine

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        sys.exit(f"✗ Cannot connect to Postgres via DATABASE_URL: {exc}")
    print("✓ DATABASE_URL connects, SECRET_KEY present")

    # 2. + 3. Column/index backfills for databases created before these
    # model changes (create_all never ALTERs an existing table).
    print(STEP.format("2/5 Backfilling treatment_feedbacks columns"))
    from migrate_revamp import MIGRATIONS

    with engine.begin() as conn:
        for sql in MIGRATIONS:
            print(f"  {sql[:70]}")
            conn.execute(text(sql))
    print("✓ treatment_feedbacks up to date")

    print(STEP.format("3/5 Backfilling medical_records indexes"))
    from add_medical_record_indexes import STATEMENTS

    with engine.begin() as conn:
        for sql in STATEMENTS:
            print(f"  {sql[:70]}")
            conn.execute(text(sql))
    print("✓ medical_records indexes in place")

    # 4. Create missing tables (adds `users`; leaves existing tables untouched)
    print(STEP.format("4/5 Creating missing tables (users)"))
    init_db()
    tables = inspect(engine).get_table_names()
    if "users" not in tables:
        sys.exit("✗ users table was not created — check DATABASE_URL permissions")
    print(f"✓ users table present (all tables: {', '.join(sorted(tables))})")

    # 5. Seed demo accounts (idempotent; never overwrites passwords unless
    # SEED_RESET_PASSWORDS=true)
    print(STEP.format("5/5 Seeding demo users"))
    from seed_users import seed

    seed()

    print(
        "\nAll done ✔  Next steps (frontend):\n"
        "  1. .env.local must contain JWT_SECRET with the SAME value as\n"
        "     backend/.env SECRET_KEY, and must NOT set NEXT_PUBLIC_API_URL.\n"
        "  2. npm install   (pulls the `jose` dependency)\n"
        "  3. Restart BOTH servers (backend + `npx next dev`).\n"
        "  4. Log in at http://localhost:3000/login\n"
    )


if __name__ == "__main__":
    main()

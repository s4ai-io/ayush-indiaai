"""
add_medical_record_indexes.py
──────────────────────────────
Backfills the visit_date/diagnosis indexes added to MedicalRecord in models.py
onto an already-existing medical_records table. Base.metadata.create_all()
(models.init_db) only creates missing tables — it never ALTERs an existing
one — so on any DB that already has the medical_records table, the new
index=True on those columns is a no-op until this runs once.

Safe to run multiple times (CREATE INDEX IF NOT EXISTS).

Run from backend/:
    ./venv/bin/python3.11 scripts/add_medical_record_indexes.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from models import engine

STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS ix_medical_records_visit_date ON medical_records (visit_date)",
    "CREATE INDEX IF NOT EXISTS ix_medical_records_diagnosis ON medical_records (diagnosis)",
]


def run_migration() -> None:
    with engine.begin() as conn:
        for stmt in STATEMENTS:
            print(f"Running: {stmt}")
            conn.execute(text(stmt))
    print("✓ Indexes on medical_records(visit_date, diagnosis) are in place.")


if __name__ == "__main__":
    run_migration()

import os, psycopg2
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DATABASE_URL = os.getenv("DATABASE_URL")

MIGRATIONS = [
    "ALTER TABLE medical_records ADD COLUMN IF NOT EXISTS parent_visit_id VARCHAR NULL",
    "ALTER TABLE medical_records ADD COLUMN IF NOT EXISTS bpm INTEGER NULL",
    "ALTER TABLE medical_records ADD COLUMN IF NOT EXISTS sugar_level DOUBLE PRECISION NULL",
    "ALTER TABLE medical_records ADD COLUMN IF NOT EXISTS spo2 INTEGER NULL",
    "ALTER TABLE medical_records ADD COLUMN IF NOT EXISTS temperature DOUBLE PRECISION NULL",
    "ALTER TABLE medical_records ADD COLUMN IF NOT EXISTS systolic_bp INTEGER NULL",
    "ALTER TABLE medical_records ADD COLUMN IF NOT EXISTS diastolic_bp INTEGER NULL",
    "CREATE INDEX IF NOT EXISTS ix_medical_records_parent_visit_id ON medical_records (parent_visit_id)",
]

def run():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    for sql in MIGRATIONS:
        print(f"Running: {sql[:70]}...")
        cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    run()

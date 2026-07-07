import os, psycopg2
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DATABASE_URL = os.getenv("DATABASE_URL")

MIGRATIONS = [
    "ALTER TABLE clinical_outcome_scores ADD COLUMN IF NOT EXISTS doctor_reported_outcome VARCHAR NULL",
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

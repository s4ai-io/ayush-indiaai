import os, psycopg2
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DATABASE_URL = os.getenv("DATABASE_URL")

MIGRATIONS = [
    "ALTER TABLE treatment_feedbacks ADD COLUMN IF NOT EXISTS original_ai_plan TEXT",
    "ALTER TABLE treatment_feedbacks ADD COLUMN IF NOT EXISTS final_plan TEXT",
    "ALTER TABLE treatment_feedbacks ADD COLUMN IF NOT EXISTS added_herbs TEXT",
    "ALTER TABLE treatment_feedbacks ADD COLUMN IF NOT EXISTS removed_herbs TEXT",
    "ALTER TABLE treatment_feedbacks ADD COLUMN IF NOT EXISTS demo_session BOOLEAN DEFAULT FALSE",
]

def run():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    for sql in MIGRATIONS:
        print(f"Running: {sql[:60]}...")
        cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    run()

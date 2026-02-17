from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Default to local postgres if env var not set
# user: utsav (from whoami), db: ayush_db
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://utsav:postgres@localhost/ayush_db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

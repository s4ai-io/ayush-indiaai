from database import engine, Base
import models_db  # Import models so they are registered with Base

def drop_tables():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped permanently.")

if __name__ == "__main__":
    drop_tables()

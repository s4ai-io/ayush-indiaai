from database import engine, Base
import models_db  # Import models so they are registered with Base

def reset_database():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped.")
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Database reset complete. All tables recreated empty.")

if __name__ == "__main__":
    reset_database()

import random
from faker import Faker
from datetime import datetime, timedelta, time
import uuid
from services.db_service import db_service
from models_db import Patient

# Initialize Faker for Indian locale
fake = Faker('en_IN')

# Constants for choices
GENDERS = ["Male", "Female", "Transgender"]
MARITAL_STATUSES = ["Married", "Unmarried", "Divorcee", "Widow"]
BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
OCCUPATIONS = ["Engineer", "Doctor", "Teacher", "Farmer", "Student", "Business", "Artist", "Homemaker", "Lawyer", "Accountant"]
ID_TYPES = ["Aadhar", "PAN Card", "Voter ID"]
STATES = ["Delhi", "Maharashtra", "Karnataka", "Gujarat", "Uttar Pradesh", "Tamil Nadu", "West Bengal", "Rajasthan"]
CITIES = {
    "Delhi": ["New Delhi", "Dwarka", "Rohini"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur"],
    "Karnataka": ["Bangalore", "Mysore", "Hubli"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
    "West Bengal": ["Kolkata", "Howrah", "Siliguri"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur"]
}

def generate_id_number(id_type):
    if id_type == "Aadhar":
        return f"{random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}"
    elif id_type == "PAN Card":
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        digits = "0123456789"
        return f"{''.join(random.choices(chars, k=5))}{''.join(random.choices(digits, k=4))}{random.choice(chars)}"
    elif id_type == "Voter ID":
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        digits = "0123456789"
        return f"{''.join(random.choices(chars, k=3))}{''.join(random.choices(digits, k=7))}"
    return "UNKNOWN"

def generate_random_timestamp(start_date, end_date):
    """
    Generate a random datetime between start_date and end_date.
    start_date and end_date should be formatted as 'YYYY-MM-DD'.
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Calculate difference in seconds
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    
    # Random second offset
    random_second = random.randrange(int_delta)
    
    return start + timedelta(seconds=random_second)

def main():
    print("Generating 1000 historical patient records (2026-02-01 to 2026-02-16)...")
    
    # Target date range
    START_DATE = "2026-02-01"
    END_DATE = "2026-02-17"
    
    count = 0
    try:
        for _ in range(1000):
            # Generate Basic Data
            gender = random.choice(GENDERS)
            first_name = fake.first_name_male() if gender == "Male" else fake.first_name_female()
            if gender == "Transgender": first_name = fake.first_name()
            last_name = fake.last_name()
            
            state = random.choice(STATES)
            city = random.choice(CITIES.get(state, [fake.city()]))
            id_type = random.choice(ID_TYPES)
            
            # Generate Random Historical Timestamp
            created_at_ts = generate_random_timestamp(START_DATE, END_DATE)
            
            # Instantiate Patient Model Directly (to set created_at)
            new_patient = Patient(
                id=uuid.uuid4(),
                first_name=first_name,
                last_name=last_name,
                gender=gender,
                age=random.randint(18, 90),
                marital_status=random.choice(MARITAL_STATUSES),
                
                mobile=f"{random.randint(6000000000, 9999999999)}",
                address=fake.street_address(),
                city=city,
                state=state,
                pincode=f"{random.randint(110000, 999999)}",
                
                blood_group=random.choice(BLOOD_GROUPS),
                occupation=random.choice(OCCUPATIONS),
                id_type=id_type,
                id_number=generate_id_number(id_type),
                
                created_at=created_at_ts,
                updated_at=created_at_ts # Assumption: created and last updated at the same time for historical data
            )
            
            db_service.db.add(new_patient)
            count += 1
            
            if count % 100 == 0:
                print(f"Generated {count} records...")
        
        # Commit all changes
        db_service.db.commit()
        print(f"Successfully committed {count} patient records to the database.")
        
    except Exception as e:
        db_service.db.rollback()
        print(f"Error occurred: {e}")
    finally:
        db_service.db.close()

if __name__ == "__main__":
    main()

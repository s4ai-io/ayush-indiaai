import os
import json
import random
from faker import Faker
from services.db_service import db_service
from database import engine, Base

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
        # 5 letters, 4 digits, 1 letter
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        digits = "0123456789"
        return f"{''.join(random.choices(chars, k=5))}{''.join(random.choices(digits, k=4))}{random.choice(chars)}"
    elif id_type == "Voter ID":
        # 3 letters, 7 digits usually
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        digits = "0123456789"
        return f"{''.join(random.choices(chars, k=3))}{''.join(random.choices(digits, k=7))}"
    return "UNKNOWN"

def generate_patient_data():
    gender = random.choice(GENDERS)
    first_name = fake.first_name_male() if gender == "Male" else fake.first_name_female()
    if gender == "Transgender": first_name = fake.first_name()
    last_name = fake.last_name()
    
    state = random.choice(STATES)
    city = random.choice(CITIES.get(state, [fake.city()]))
    
    id_type = random.choice(ID_TYPES)
    
    return {
        "basicInfo": {
            "firstName": first_name,
            "lastName": last_name,
            "gender": gender,
            "age": random.randint(18, 90),
            "maritalStatus": random.choice(MARITAL_STATUSES),
            "nationality": "Indian"
        },
        "contactInfo": {
            "mobileNumber": f"{random.randint(6000000000, 9999999999)}",
            "address": fake.street_address(),
            "city": city,
            "state": state,
            "pincode": f"{random.randint(110000, 999999)}"
        },
        "otherInfo": {
            "occupation": random.choice(OCCUPATIONS),
            "bloodGroup": random.choice(BLOOD_GROUPS),
            "idType": id_type,
            "idNumber": generate_id_number(id_type)
        }
    }

def main():
    print("Initializing Database Tables...")
    Base.metadata.create_all(bind=engine)
    
    print("Generating 100 synthetic patients...")
    patients_list = []
    
    # 1. Generate Data
    for _ in range(100):
        data = generate_patient_data()
        patients_list.append(data)
        
        # 2. Insert into DB
        try:
            db_service.create_patient(
                basic_info=data["basicInfo"],
                contact_info=data["contactInfo"],
                other_info=data["otherInfo"]
            )
        except Exception as e:
            print(f"Error inserting patient: {e}")

    # 3. Save to registrations.json
    json_path = "../data/registrations.json"
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(patients_list, f, indent=4)
        
    print(f"✓ 100 patients generated and saved to DB and {json_path}")

if __name__ == "__main__":
    main()

"""
name_pool.py
─────────────
Regionally-weighted Indian name pools for the v2 synthetic data generator.

The original generator drew from a single flat list of 27 male first names, 27
female first names and 28 surnames for all 800 patients regardless of which
city/state they were assigned — guaranteed heavy repetition across patients,
and a Tamil Nadu patient was just as likely to be named "Amit Sharma" as a
Punjab patient. This module groups ~40 first names per gender and ~40 surnames
per linguistic/cultural region (200+ total per list, matching the actual
regional-name diversity a pan-India clinic network would see), and picks
mostly from a patient's own region with a small chance of an out-of-region
name (realistic given internal migration).
"""
from __future__ import annotations

import random

REGIONS = ["north", "west", "south", "east", "northeast"]

# Maps geo_reference.py state names to a naming region.
STATE_TO_REGION: dict[str, str] = {
    # North (Hindi/Punjabi/Kashmiri/Himachali/Dogri belt + Hindi-belt Central states)
    "Delhi": "north", "Haryana": "north", "Punjab": "north", "Chandigarh": "north",
    "Himachal Pradesh": "north", "Jammu and Kashmir": "north", "Ladakh": "north",
    "Uttar Pradesh": "north", "Uttarakhand": "north",
    "Madhya Pradesh": "north", "Chhattisgarh": "north",
    # West
    "Maharashtra": "west", "Gujarat": "west", "Rajasthan": "west", "Goa": "west",
    # South
    "Tamil Nadu": "south", "Kerala": "south", "Karnataka": "south",
    "Andhra Pradesh": "south", "Telangana": "south", "Puducherry": "south",
    # East
    "West Bengal": "east", "Odisha": "east", "Bihar": "east", "Jharkhand": "east",
    # Northeast
    "Assam": "northeast", "Manipur": "northeast", "Meghalaya": "northeast",
    "Tripura": "northeast", "Mizoram": "northeast", "Nagaland": "northeast",
    "Arunachal Pradesh": "northeast", "Sikkim": "northeast",
}

FIRST_NAMES_M: dict[str, list[str]] = {
    "north": [
        "Amit", "Rajesh", "Vikram", "Suresh", "Pradeep", "Manoj", "Dinesh", "Ramesh",
        "Anil", "Ajay", "Sanjay", "Rohit", "Nitin", "Kiran", "Mahesh", "Deepak",
        "Vivek", "Ashok", "Pramod", "Girish", "Hemant", "Naresh", "Santosh", "Vinod",
        "Ravi", "Sunil", "Arun", "Mohan", "Gurpreet", "Harpreet", "Jaspreet",
        "Baldev", "Kuldeep", "Manpreet", "Rajinder", "Surinder", "Tejinder",
        "Yashpal", "Randhir", "Devendra", "Satpal", "Brij Mohan",
    ],
    "west": [
        "Sachin", "Rahul", "Nikhil", "Sameer", "Prakash", "Vasant", "Yogesh",
        "Sandip", "Milind", "Chetan", "Kishor", "Anand", "Vishal", "Rajendra",
        "Bhushan", "Ganesh", "Uday", "Shrikant", "Vaibhav", "Prashant", "Jignesh",
        "Bhavesh", "Ketan", "Nirav", "Rakesh", "Ashish", "Paresh", "Mehul",
        "Hitesh", "Dharmesh", "Kalpesh", "Vipul", "Jayesh", "Pravin", "Bharat",
        "Vijay", "Kantilal", "Shantilal", "Mangesh", "Sadanand",
    ],
    "south": [
        "Karthik", "Arun Kumar", "Vijay Kumar", "Ramesh Babu", "Senthil", "Balaji",
        "Murugan", "Elango", "Gopinath", "Krishnamurthy", "Venkatesh", "Raghavan",
        "Subramaniam", "Natarajan", "Manikandan", "Ravichandran", "Sivakumar",
        "Chandrasekhar", "Srinivasan", "Gopalakrishnan", "Padmanabhan", "Rajagopal",
        "Ranganathan", "Selvam", "Kumaresan", "Prabhakaran", "Jayaraman",
        "Nagarajan", "Shanmugam", "Velmurugan", "Arjun", "Sathish", "Ganesan",
        "Muthukumar", "Ashwin", "Praveen Kumar", "Suresh Kumar", "Dinesh Kumar",
        "Vijayan", "Rajesh Kanna",
    ],
    "east": [
        "Suman", "Debashish", "Partha", "Tapan", "Ashoke", "Subrata", "Amitava",
        "Bimal", "Gautam", "Sourav", "Abhijit", "Anirban", "Biplab", "Chandan",
        "Goutam", "Himangshu", "Jayanta", "Kaushik", "Manas", "Niranjan",
        "Prasenjit", "Sudip", "Tanmoy", "Uttam", "Bibhuti", "Chittaranjan",
        "Bijoy", "Ranjit", "Sourabh", "Swapan", "Bikash", "Pranab", "Satyajit",
        "Dulal", "Mrinal Kanti", "Provat", "Sudhir Ranjan", "Barun",
    ],
    "northeast": [
        "Bhaskar", "Dipankar", "Hemanta", "Jyotish", "Kamal Kumar", "Lakhi",
        "Manoranjan", "Nabin", "Probin", "Ranjan", "Sailen", "Tridip", "Ananta",
        "Bipul", "Deven", "Hiranya", "Indrajit", "Jibon", "Loknath", "Mrinal",
        "Nripen", "Prasanta", "Rupam", "Sarat", "Utpal", "Bhupen", "Diganta",
        "Jadav", "Munin", "Pranjal", "Rajib", "Sanjib", "Tapan Baruah",
        "Zohmingliana", "Lalrinchhana", "Temjen", "Akum", "Toshi",
        "Bipin Chandra", "Debojit", "Girin", "Kailash Bora", "Lakshya",
        "Nayan Jyoti", "Rituraj", "Simanta",
    ],
}

FIRST_NAMES_F: dict[str, list[str]] = {
    "north": [
        "Priya", "Sunita", "Meera", "Kavita", "Rekha", "Asha", "Neha", "Pooja",
        "Sonal", "Anjali", "Shweta", "Ritu", "Puja", "Anita", "Geeta", "Lata",
        "Nisha", "Pallavi", "Archana", "Divya", "Manisha", "Seema", "Usha",
        "Vandana", "Madhuri", "Jyoti", "Sarita", "Simran", "Gurmeet Kaur",
        "Harpreet Kaur", "Amandeep Kaur", "Jaspreet Kaur", "Rajwinder Kaur",
        "Sudesh", "Kamlesh", "Vimla", "Savita", "Renu", "Poonam", "Rajni",
    ],
    "west": [
        "Snehal", "Manasi", "Aarti", "Swati", "Vaishali", "Trupti", "Kranti",
        "Sonali", "Rupali", "Shilpa", "Deepali", "Madhavi", "Sujata", "Varsha",
        "Yamini", "Falguni", "Bhavna", "Nirali", "Krupa", "Payal", "Foram",
        "Dipti", "Heena", "Nita", "Rita", "Priti", "Kajal", "Komal", "Riya",
        "Meenakshi", "Hansaben", "Jyotsna", "Sushma", "Aparna", "Rutuja",
        "Ashwini", "Vidya", "Manjusha", "Sarika",
    ],
    "south": [
        "Lakshmi", "Meenakshi", "Kavya", "Divya", "Priyanka", "Deepa", "Radha",
        "Saroja", "Kalyani", "Vasantha", "Padma", "Rajeshwari", "Sujatha", "Vani",
        "Uma", "Vidya", "Bhavani", "Chitra", "Indira", "Jayanthi", "Kamala",
        "Malathi", "Nirmala", "Parvathi", "Revathi", "Shanthi", "Suganya",
        "Swathi", "Vaidehi", "Yamuna", "Anitha", "Bhuvana", "Devika", "Geetha",
        "Hema", "Janaki", "Kavitha", "Nithya", "Pushpa", "Sowmya",
    ],
    "east": [
        "Sharmila", "Debjani", "Piyali", "Ratna", "Ananya", "Bidisha", "Chandrima",
        "Doyel", "Ipsita", "Jayasree", "Kakoli", "Lopamudra", "Mahua", "Nandini",
        "Oindrila", "Payel", "Rina", "Sohini", "Titli", "Urmi", "Bandana",
        "Chaitali", "Dipa", "Gargi", "Hasi", "Ila", "Juthika", "Kabita",
        "Malabika", "Namrata", "Purabi", "Rupa", "Sagarika", "Tripti",
        "Bharati", "Chhaya", "Debolina", "Moushumi",
    ],
    "northeast": [
        "Anamika", "Barsha", "Chandana", "Deepika", "Elizabeth", "Farida",
        "Gitashree", "Himashree", "Indrani", "Junmoni", "Kabita", "Lakhimi",
        "Monalisa", "Nayanmoni", "Pallabi", "Rashmi Rekha", "Sangeeta", "Trishna",
        "Urvashi", "Champa", "Dolly", "Farheen", "Gunjan", "Hiya", "Ivy",
        "Jonali", "Kasturi", "Meghna", "Nishita", "Parismita", "Rimjhim",
        "Snigdha", "Tulika", "Angelina", "Beauty", "Diana", "Grace", "Rosemary",
        "Bornali", "Dimpi", "Elora", "Karishma Bora", "Mousumi", "Priyakshi",
        "Rukmini", "Suravi", "Tanushree", "Yasmin",
    ],
}

LAST_NAMES: dict[str, list[str]] = {
    "north": [
        "Sharma", "Gupta", "Verma", "Singh", "Kumar", "Chauhan", "Tiwari",
        "Mishra", "Pandey", "Agarwal", "Srivastava", "Dubey", "Bhatt", "Yadav",
        "Rathore", "Rawat", "Bisht", "Bhandari", "Malhotra", "Kapoor", "Khanna",
        "Chopra", "Anand", "Bedi", "Sethi", "Bhalla", "Grover", "Ahluwalia",
        "Sodhi", "Brar", "Sandhu", "Dhillon", "Gill", "Sidhu", "Sekhon",
        "Chahal", "Kalra", "Aggarwal", "Bansal", "Goyal", "Saxena", "Trivedi",
    ],
    "west": [
        "Patel", "Shah", "Desai", "Mehta", "Joshi", "Pawar", "More", "Patil",
        "Kulkarni", "Deshmukh", "Jadhav", "Chavan", "Gaikwad", "Bhosale",
        "Kadam", "Sawant", "Naik", "Rane", "Salunkhe", "Thakur", "Vora",
        "Pandya", "Parekh", "Modi", "Shroff", "Doshi", "Gandhi", "Rathi",
        "Bafna", "Kothari", "Oswal", "Lodha", "Amin", "Nanda", "Bhagat",
        "Shukla", "Dave", "Chokshi", "Vaidya", "Kelkar",
    ],
    "south": [
        "Iyer", "Iyengar", "Nair", "Menon", "Pillai", "Reddy", "Rao", "Naidu",
        "Chetty", "Gowda", "Shetty", "Bhat", "Hegde", "Kamath", "Pai", "Acharya",
        "Krishnan", "Subramaniam", "Venkataraman", "Raman", "Sundaram",
        "Balakrishnan", "Ramanathan", "Varma", "Warrier", "Namboothiri",
        "Panicker", "Kurup", "Nambiar", "Chandran", "Naicker", "Chettiar",
        "Mudaliar", "Ganapathy", "Ramamurthy", "Achari", "Reddiar",
    ],
    "east": [
        "Banerjee", "Mukherjee", "Chatterjee", "Bose", "Ghosh", "Das", "Sen",
        "Dutta", "Roy", "Chakraborty", "Sarkar", "Bhattacharya", "Mitra", "Pal",
        "Guha", "Choudhury", "Majumdar", "Kar", "Nandi", "Adhikari", "Biswas",
        "Halder", "Sengupta", "Mondal", "Bagchi", "Dey", "Ganguly", "Basu",
        "Lahiri", "Sanyal", "Mahato", "Behera", "Patra", "Panda", "Mohanty",
        "Nayak", "Sahoo", "Rout", "Pradhan", "Sahu",
    ],
    "northeast": [
        "Gogoi", "Baruah", "Bora", "Saikia", "Hazarika", "Kalita", "Deka",
        "Phukan", "Bhuyan", "Doley", "Boruah", "Neog", "Handique", "Bordoloi",
        "Konwar", "Mahanta", "Rajkhowa", "Barman", "Sarma", "Momin", "Marak",
        "Sangma", "Lyngdoh", "Khongsit", "Marbaniang", "Ralte", "Lalrinawma",
        "Sailo", "Zeliang", "Ao", "Longkumer", "Imchen", "Chishi",
        "Khiamniungan", "Lotha", "Sema", "Yimchunger", "Chutia", "Kachari",
        "Rabha", "Tanti", "Baishya", "Bhagawati",
    ],
}


def _pick(pool_by_region: dict[str, list[str]], state: str, rng: random.Random | None = None) -> str:
    r = rng or random
    region = STATE_TO_REGION.get(state, "north")
    # 85% own region, 15% national pool (internal migration realism)
    if r.random() < 0.85:
        return r.choice(pool_by_region[region])
    return r.choice(pool_by_region[r.choice(REGIONS)])


def sample_first_name(gender: str, state: str, rng: random.Random | None = None) -> str:
    pool = FIRST_NAMES_M if gender == "Male" else FIRST_NAMES_F
    return _pick(pool, state, rng)


def sample_last_name(state: str, rng: random.Random | None = None) -> str:
    return _pick(LAST_NAMES, state, rng)

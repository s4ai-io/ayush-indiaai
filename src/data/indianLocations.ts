// Top states/UTs and their major cities across India, used to drive the
// State → City cascading selects on the registration form. Kept in sync
// with the state/city enums baked into the voice-agent prompts
// (backend/services/registration_agent.py and
// backend/modal_script/modal_gemma4_12b.py) — update all three together.
export const INDIAN_STATE_CITY_MAP: Record<string, string[]> = {
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Tirupati", "Nellore"],
    "Assam": ["Guwahati", "Dibrugarh", "Silchar", "Jorhat"],
    "Bihar": ["Patna", "Gaya", "Bhagalpur", "Muzaffarpur"],
    "Chhattisgarh": ["Raipur", "Bhilai", "Bilaspur", "Durg"],
    "Delhi": ["New Delhi", "Dwarka", "Rohini", "Karol Bagh", "Connaught Place"],
    "Goa": ["Panaji", "Margao", "Vasco da Gama"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Gandhinagar"],
    "Haryana": ["Gurugram", "Faridabad", "Panipat", "Ambala"],
    "Jammu and Kashmir": ["Srinagar", "Jammu"],
    "Jharkhand": ["Ranchi", "Jamshedpur", "Dhanbad", "Bokaro"],
    "Karnataka": ["Bangalore", "Mysore", "Mangalore", "Hubli", "Belgaum"],
    "Kerala": ["Kochi", "Thiruvananthapuram", "Kozhikode", "Thrissur"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Gwalior", "Jabalpur", "Ujjain"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Thane", "Aurangabad"],
    "Odisha": ["Bhubaneswar", "Cuttack", "Rourkela"],
    "Punjab": ["Chandigarh", "Amritsar", "Ludhiana", "Jalandhar", "Patiala"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Ajmer"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirapalli", "Salem"],
    "Telangana": ["Hyderabad", "Warangal", "Nizamabad"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Agra", "Noida", "Ghaziabad", "Prayagraj"],
    "Uttarakhand": ["Dehradun", "Haridwar", "Rishikesh"],
    "West Bengal": ["Kolkata", "Howrah", "Durgapur", "Siliguri", "Asansol"],
};

export const INDIAN_STATES = Object.keys(INDIAN_STATE_CITY_MAP).sort();

export const ALL_INDIAN_CITIES = Object.values(INDIAN_STATE_CITY_MAP).flat().sort();

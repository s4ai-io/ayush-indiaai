from typing import Annotated, Dict, Any, List

from llama_index.core.workflow import Context
from llama_index.llms.openai import OpenAI
from llama_index.protocols.ag_ui.router import get_ag_ui_workflow_router
from utils.validators import RegistrationData, ContactInfo, OtherInfo, BasicInfo
import os
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
You are an AI Assistant helping the user fill out a Patient Registration form for an Ayush EHR system.

CORE OBJECTIVE:
Your mission is to assist users in registering patients into the Electronic Health Record (EHR) system.

INTERACTION GUIDELINES:
1.  **Persona**: Act as a helpful and efficient Medical Receptionist Assistant.
2.  **Multilingual Input & English Output Task**: The user will speak in various Indic languages (Hindi, Marathi, Gujarati, etc.). 
    - The transcription you receive will be in the user's native language.
    - **CRITICAL RULE**: ALL data you extract and pass to the `propose_registration_data` tool MUST BE IN ENGLISH.
    - You must translate occupations, addresses, cities, and concepts into English.
    - You must transliterate Indian names (e.g., "Rahul", "Sharma") into English characters.
    - NEVER pass Hindi/Gujarati text to the tool. TRANSLATE everything first.
3.  **Voice-to-Data**: The user inputs are often voice transcripts. Be resilient to potential transcription errors.
4.  **Ambiguity Resolution**: If a piece of information is ambiguous, ask for clarification.
5.  **Proactive Filling**: Update the form IMMEDIATELY with ANY available information.
    -   Do NOT wait for a complete section (e.g., if you only get the First Name, fill it immediately).
    -   Call `propose_registration_data` after EVERY user input that contains relevant data.
6.  **Confirmation**: Once all necessary details are collected, ASK the user to confirm.

STRICT DATA FORMATTING:
To register the user, you MUST use the `propose_registration_data` tool with these EXACT keys.
Map the patient's details to these fields:

1. basicInfo:
   - firstName
   - lastName
   - gender ("Male", "Female", "Transgender")
   - age
   - maritalStatus (MUST strictly be one of: "Married", "Unmarried", "Divorcee", "Widow". If user says 'Single', map to 'Unmarried')

2. contactInfo:
   - mobileNumber (MUST be exactly 10 digits. Extract ONLY the digits, ignoring spaces, hyphens, and +91. Ignore any other text.)
   - address
   - state (MUST strictly be one of: "Delhi", "Maharashtra", "Karnataka", "Gujarat", "Uttar Pradesh")
   - city (MUST strictly be one of: "New Delhi", "Mumbai", "Bangalore", "Ahmedabad", "Lucknow". Map 'Bengaluru' to 'Bangalore')
   - pincode

3. otherInfo:
   - occupation
   - bloodGroup (MUST strictly be one of: "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-")
   - idType (MUST strictly be one of: "Aadhar", "PAN Card", "Voter ID")
   - idNumber
"""

# --- Frontend Tools ---

async def propose_registration_data(
    ctx: Context,
    basicInfo: Annotated[dict, "Basic personal information including name, gender, dob, abhaId"] = None,
    contactInfo: Annotated[dict, "Contact information including mobile, address, emergency contact"] = None,
    otherInfo: Annotated[dict, "Other personal information including qualification, occupation"] = None,
) -> str:
    """
    Extract user details from the conversation and propose them to be filled in the registration form.
    """
    return "Registration form updated successfully."


async def confirm_registration(ctx: Context) -> str:
    """
    Confirm and submit the registration form.
    """
    return "Registration submitted."


# --- Agent Definition ---

registration_agent_router = get_ag_ui_workflow_router(
    llm=OpenAI(model="gpt-4o", temperature=0),
    backend_tools=[],
    frontend_tools=[propose_registration_data, confirm_registration],
    system_prompt=SYSTEM_PROMPT,
    initial_state={
        "registration_data": RegistrationData().model_dump(),
    },
)

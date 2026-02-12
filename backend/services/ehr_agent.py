from typing import Annotated, Dict, Any
from llama_index.llms.openai import OpenAI
from utils.agent.ag_ui_router import get_ag_ui_workflow_router
import os
from dotenv import load_dotenv

load_dotenv()

# --- Backend Tools ---

async def verify_patient_identity(
    patient_id: Annotated[str, "The ID of the patient"],
    name: Annotated[str, "The name of the patient"]
) -> str:
    """Verify if the patient exists in the database."""
    # Mock implementation
    return f"Verified: Patient {name} (ID: {patient_id}) exists in the system."


async def suggest_ayush_diagnosis(
    symptoms: Annotated[str, "List of symptoms described by the patient"],
    age: Annotated[int, "Age of the patient"],
    gender: Annotated[str, "Gender of the patient"]
) -> str:
    """Suggest likely diagnoses based on symptoms and demographics using AYUSH patterns."""
    # This could call the existing ML service in a real implementation
    # For now, return basic AYUSH concepts
    return f"Based on symptoms '{symptoms}', possible conditions in Ayurveda: Vata aggravation manifesting as headache. Recommended checking for indigestion (Ajirna)."


async def draft_ehr(
    patient_data: Annotated[Dict[str, Any], "Dictionary containing patient details (name, age, etc.)"],
    clinical_notes: Annotated[str, "Doctor's notes and observations"],
    diagnosis: Annotated[str, "Final diagnosis"]
) -> str:
    """Create a structured EHR draft."""
    return f"EHR Draft Created for {patient_data.get('name')}:\nDiagnosis: {diagnosis}\nNotes: {clinical_notes}\nStatus: DRAFT"


# --- Frontend Tools (Declarations) ---
# These function bodies are just placeholders/definitions for the LLM to know they exist.
# The actual execution happens on the frontend.

def update_ehr_form(
    patient_name: Annotated[str, "Patient Name"],
    age: Annotated[str, "Patient Age"],
    symptoms: Annotated[str, "Patient Symptoms"],
    diagnosis: Annotated[str, "Diagnosis"],
) -> str:
    """Updates the EHR form fields in the UI."""
    return "Form updated"


# --- Agent Definition ---

ehr_agent_router = get_ag_ui_workflow_router(
    llm=OpenAI(model="gpt-4o-mini", temperature=0),
    # Tools executed in the frontend
    frontend_tools=[update_ehr_form],
    # Tools executed in the backend
    backend_tools=[verify_patient_identity, suggest_ayush_diagnosis, draft_ehr],
    system_prompt="""You are an expert AYUSH Medical Assistant helping a doctor create an Electronic Health Record (EHR).
    
    Your goal is to:
    1. Gather patient information (Name, Age, Gender, Symptoms).
    2. Use `update_ehr_form` to fill the UI as you get information.
    3. Suggest diagnoses using `suggest_ayush_diagnosis` when symptoms are clear.
    4. Help draft the final note using `draft_ehr`.
    
    Be concise, professional, and helpful. Always try to keep the form updated with the latest information you have.""",
    initial_state={}
)

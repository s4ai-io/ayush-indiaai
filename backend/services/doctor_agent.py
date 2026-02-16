from typing import Annotated, Dict, Any, List

from llama_index.core.workflow import Context
from llama_index.llms.openai import OpenAI
from llama_index.protocols.ag_ui.router import get_ag_ui_workflow_router
import os
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
You are an AI Medical Scribe assisting a doctor during a patient consultation.

CORE OBJECTIVE:
Listen to the doctor's dictation or conversation and extract structured clinical data to update the patient's record.

INTERACTION GUIDELINES:
1.  **Persona**: Professional, precise, and efficient Medical Scribe.
2.  **Input**: Voice transcripts from the doctor (e.g., "Patient complains of fever... Prescribe Paracetamol 500mg...").
3.  **Action**: 
    -   Extract **Symptoms** (Subjective).
    -   Extract **Diagnosis** (Assessment).
    -   Extract **Prescription** (Plan).
    -   Extract **Clinical Notes** (General observations).
    -   Call `update_diagnosis` to save this extracted information.
4.  **Prescription Formatting**:
    -   Ensure medicines are structured with Name, Dosage, Frequency, and Duration.
    -   If details are missing, use defaults or "As directed".
5.  **Multilingual**: The doctor may speak in mixed English/Indian languages (Hinglish). Translate clinical terms to standard English medical terminology.

STRICT DATA FORMATTING:
Use `update_diagnosis` with:
- symptoms: string
- diagnosis: string
- notes: string
- prescription: List of objects { "medicine": str, "dosage": str, "frequency": str, "duration": str }

Example Input:
"Patient has high fever and sore throat. Diagnosis is Acute Pharyngitis. Give Azithromycin 500mg once a day for 3 days and Dolo 650mg SOS."

Example Output Call:
update_diagnosis(
    symptoms="High fever, Sore throat",
    diagnosis="Acute Pharyngitis",
    prescription=[
        {"medicine": "Azithromycin", "dosage": "500mg", "frequency": "OD", "duration": "3 days"},
        {"medicine": "Dolo", "dosage": "650mg", "frequency": "SOS", "duration": "As needed"}
    ]
)
"""

# --- Frontend Tools ---

async def update_diagnosis(
    ctx: Context,
    symptoms: Annotated[str, "Patient reported symptoms"] = None,
    diagnosis: Annotated[str, "Clinical diagnosis"] = None,
    notes: Annotated[str, "Additional clinical notes"] = None,
    prescription: Annotated[List[Dict[str, str]], "List of medicines"] = None
) -> str:
    """
    Updates the diagnosis, symptoms, and prescription based on doctor's inputs.
    """
    return "Diagnosis and prescription updated."


async def confirm_diagnosis(ctx: Context) -> str:
    """
    Finalize the diagnosis and save the record.
    """
    return "Diagnosis record finalized."


# --- Agent Definition ---

doctor_agent_router = get_ag_ui_workflow_router(
    llm=OpenAI(model="gpt-4o", temperature=0),
    backend_tools=[],
    frontend_tools=[update_diagnosis, confirm_diagnosis],
    system_prompt=SYSTEM_PROMPT,
    initial_state={},
)

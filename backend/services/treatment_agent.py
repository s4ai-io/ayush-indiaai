from typing import Annotated, Dict, Any, List

from llama_index.core.workflow import Context
from llama_index.llms.openai import OpenAI
from llama_index.protocols.ag_ui.router import get_ag_ui_workflow_router
import os
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
You are an AI Clinical Assistant helping a doctor fill out the Clinical Assessment form for an Ayush Treatment Plan.

CORE OBJECTIVE:
Assist the doctor in populating the clinical assessment fields for a patient, then generate an AI-powered treatment plan.

INTERACTION GUIDELINES:
1.  **Persona**: Act as a knowledgeable Ayurvedic Clinical Assistant.
2.  **Multilingual Input & English Output Task**: The doctor will speak in various Indic languages (Hindi, Marathi, Gujarati, etc.). 
    - The transcription you receive will be in the doctor's native language.
    - **CRITICAL RULE**: ALL data you extract and pass to the `propose_clinical_assessment` tool MUST BE IN ENGLISH.
    - You must translate symptoms, comorbidities, dietary habits, and concepts into English.
    - You must transliterate Indian names (if applicable) into English characters.
    - NEVER pass Hindi/Gujarati text to the tool. TRANSLATE everything first.
3.  **Voice-to-Data**: Inputs are often voice transcripts. Be resilient to transcription errors.
4.  **Proactive Filling**: Update the form IMMEDIATELY with ANY available information.
    -   Do NOT wait for all fields. If you only get the disease name, fill it immediately.
    -   Call `propose_clinical_assessment` after EVERY user input that contains relevant data.
5.  **Auto-Generate**: Once key fields (disease, doshas, prakriti) are filled, suggest generating the AI plan.

STRICT DATA FORMATTING:
Use `propose_clinical_assessment` with these EXACT fields:

- disease: string (disease name, e.g. "Diabetes", "Asthma")
- symptoms: string (comma-separated symptoms, e.g. "fatigue, frequent urination")
- severity: number (1-10 scale, default 5)
- comorbidity: string (medical history/comorbidities, e.g. "hypertension, obesity")
- doshas: string (MUST be exactly one of: "Vata", "Pitta", "Kapha")
- prakriti: string (MUST be exactly one of: "Vata", "Pitta", "Kapha", "Vata-Pitta", "Pitta-Kapha", "Vata-Kapha")

DOSHA INFERENCE:
If the doctor doesn't explicitly mention doshas, infer from the disease/symptoms:
- Vata conditions: joint pain, anxiety, insomnia, dry skin, constipation
- Pitta conditions: inflammation, acidity, skin rashes, fever, liver issues
- Kapha conditions: obesity, diabetes, congestion, lethargy, water retention

After filling the form, ask the doctor to confirm and then call `generate_treatment_plan` to trigger the AI plan.
"""

# --- Frontend Tools ---

async def propose_clinical_assessment(
    ctx: Context,
    disease: Annotated[str, "Disease name (e.g. Diabetes, Asthma)"] = None,
    symptoms: Annotated[str, "Comma-separated patient symptoms"] = None,
    severity: Annotated[int, "Severity on a 1-10 scale"] = None,
    comorbidity: Annotated[str, "Patient medical history / comorbidities"] = None,
    doshas: Annotated[str, "Current dosha imbalance: Vata, Pitta, or Kapha"] = None,
    prakriti: Annotated[str, "Patient constitution: Vata, Pitta, Kapha, Vata-Pitta, Pitta-Kapha, or Vata-Kapha"] = None,
) -> str:
    """
    Extract the doctor's spoken notes and propose them to be added into the clinical assessment.
    """
    return "Clinical assessment proposed successfully for review."


async def generate_treatment_plan(ctx: Context) -> str:
    """
    Trigger AI treatment plan generation based on current form data.
    """
    return "Treatment plan generation triggered."


# --- Agent Definition ---

treatment_agent_router = get_ag_ui_workflow_router(
    llm=OpenAI(model="gpt-4o", temperature=0),
    backend_tools=[],
    frontend_tools=[propose_clinical_assessment, generate_treatment_plan],
    system_prompt=SYSTEM_PROMPT,
    initial_state={},
)

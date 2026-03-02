from typing import Annotated, Dict, Any, List

from llama_index.core.workflow import Context
from llama_index.protocols.ag_ui.router import get_ag_ui_workflow_router
from utils.llm_config import get_llm
from config import AGENT_TIMEOUT
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

STRICT DATA FORMATTING:
Use `propose_clinical_assessment` with these EXACT fields:

- disease: string (disease name, e.g. "Diabetes", "Asthma")
- symptoms: string (comma-separated symptoms, e.g. "fatigue, frequent urination")
- comorbidity: string (medical history/comorbidities, e.g. "hypertension, obesity")
- vikriti: string (MUST be exactly one of: "Vata", "Pitta", "Kapha")
- prakriti: string (MUST be exactly one of: "Vata", "Pitta", "Kapha", "Vata-Pitta", "Pitta-Kapha", "Vata-Kapha")
- herbs: string (comma-separated herbs suggested by the doctor e.g. "Ashwagandha, Tulsi")
- yoga: string (comma-separated yoga practices suggested by the doctor e.g. "Surya Namaskar, Pranayama")
- diet: string (comma-separated dietary suggestions e.g. "Avoid spicy food, drink warm water")
- lifestyle: string (comma-separated lifestyle suggestions e.g. "Sleep early, avoid day sleep")

DOSHA INFERENCE:
If the doctor doesn't explicitly mention doshas, infer from the disease/symptoms:
- Vata conditions: joint pain, anxiety, insomnia, dry skin, constipation
- Pitta conditions: inflammation, acidity, skin rashes, fever, liver issues
- Kapha conditions: obesity, diabetes, congestion, lethargy, water retention

After filling the form, ask the doctor to review the UI and click the Generate button manually. Do NOT attempt to generate it yourself.
"""

# --- Frontend Tools ---

async def propose_clinical_assessment(
    ctx: Context,
    disease: Annotated[str, "Disease name (e.g. Diabetes, Asthma)"] = None,
    symptoms: Annotated[str, "Comma-separated patient symptoms"] = None,
    comorbidity: Annotated[str, "Patient medical history / comorbidities"] = None,
    vikriti: Annotated[str, "Current dosha imbalance: Vata, Pitta, or Kapha"] = None,
    prakriti: Annotated[str, "Patient constitution: Vata, Pitta, Kapha, Vata-Pitta, Pitta-Kapha, or Vata-Kapha"] = None,
    herbs: Annotated[str, "Comma-separated doctor prescribed herbs"] = None,
    yoga: Annotated[str, "Comma-separated doctor prescribed yoga practices"] = None,
    diet: Annotated[str, "Comma-separated doctor prescribed diet suggestions"] = None,
    lifestyle: Annotated[str, "Comma-separated doctor prescribed lifestyle suggestions"] = None,
) -> str:
    """
    Extract the doctor's spoken notes and propose them to be added into the clinical assessment.
    """
    return "Clinical assessment proposed successfully for review."

# --- Agent Definition ---

treatment_agent_router = get_ag_ui_workflow_router(
    llm=get_llm(),
    backend_tools=[],
    frontend_tools=[propose_clinical_assessment],
    system_prompt=SYSTEM_PROMPT,
    initial_state={},
    timeout=AGENT_TIMEOUT,
)

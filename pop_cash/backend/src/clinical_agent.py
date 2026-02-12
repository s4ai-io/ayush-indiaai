from typing import Annotated, Dict, Any

from llama_index.core.workflow import Context
from llama_index.llms.openai import OpenAI
from llama_index.protocols.ag_ui.router import get_ag_ui_workflow_router
from src.models import EHRDraft, ConfidenceScores, ClinicalResponse

# Use a global dictionary to simulate session-based storage for the EHR draft
# In a real app, this would be a database or Redis
# Key: session_id/thread_id, Value: EHRDraft
EHR_DRAFT_STORE: Dict[str, EHRDraft] = {}

SYSTEM_PROMPT = """
You are an AI Clinical Copilot (AGUI) designed to assist AYUSH healthcare professionals in creating accurate, structured, and compliant Electronic Health Records (EHRs) using voice-based inputs (simulated as text).

CORE RESPONSIBILITIES:
1.  **Voice-First Clinical Documentation**: Convert input into structured clinical data.
2.  **Structured EHR Creation**: Populate patient demographics, complaints, findings, diagnosis (AYUSH-specific), prakriti, etc.
3.  **AYUSH Context Awareness**: Recognize Vata/Pitta/Kapha, AYUSH therapies, and terminology.
4.  **Human-in-the-Loop Safety**: Always clarify missing info. Do NOT hallucinate.

INTERACTION GUIDELINES:
-   Listen passively.
-   Extract data into the `EHRDraft` structure.
-   If info is missing, ask specific clarifying questions.
-   Do NOT generate treatment recommendations unless explicitly asked.

When you receive information, use the `update_ehr_draft` tool to update the structured record.
Always verify the current state of the draft before asking for more info.
"""

async def update_ehr_draft(
    ctx: Context,
    demographics: Annotated[dict, "Patient demographics"] = None,
    presenting_complaints: Annotated[list, "List of complaints"] = None,
    clinical_findings: Annotated[list, "List of clinical findings"] = None,
    diagnosis: Annotated[list, "List of diagnoses"] = None,
    prakriti: Annotated[dict, "Prakriti assessment"] = None,
    comorbidities: Annotated[list, "List of comorbidities"] = None,
    therapies: Annotated[list, "List of therapies"] = None,
    lifestyle_advice: Annotated[list, "List of lifestyle advice"] = None,
    follow_up: Annotated[str, "Follow-up instructions"] = None,
) -> str:
    """
    Updates the current EHR draft with the provided information. 
    Only provide fields that need to be updated.
    """
    # This function is executed on the frontend via useCopilotAction.
    # The return value here is just for the LLM to see "tool executed".
    return "EHR Draft updated successfully."

clinical_agent_router = get_ag_ui_workflow_router(
    llm=OpenAI(model="gpt-4o"), 
    
    # Tools executed in backend (updating the draft state)
    backend_tools=[],
    
    # Tools executed in frontend client
    frontend_tools=[update_ehr_draft],
    
    system_prompt=SYSTEM_PROMPT,
    
    initial_state={
        "ehr_draft": EHRDraft().model_dump(),
        "confidence_scores": ConfidenceScores().model_dump(),
        "clarifications_required": []
    },
)

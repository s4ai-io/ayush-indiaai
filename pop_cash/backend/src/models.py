from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

class Demographics(BaseModel):
    name: Optional[str] = Field(None, description="Patient's full name")
    age: Optional[Union[str, int]] = Field(None, description="Patient's age")
    gender: Optional[str] = Field(None, description="Patient's gender")
    contact: Optional[str] = Field(None, description="Contact information")
    uhid: Optional[str] = Field(None, description="Unique Health ID if available")

class PresentingComplaint(BaseModel):
    symptom: str = Field(..., description="The main complaint or symptom")
    duration: Optional[str] = Field(None, description="How long the symptom has persisted")
    severity: Optional[str] = Field(None, description="Severity of the symptom (mild, moderate, severe)")
    notes: Optional[str] = Field(None, description="Additional notes")

class ClinicalFinding(BaseModel):
    observation: str = Field(..., description="Objective clinical finding")
    category: Optional[str] = Field(None, description="Category (General, Systemic, Local)")

class Diagnosis(BaseModel):
    condition: str = Field(..., description="Diagnosed condition or disease")
    icd_code: Optional[str] = Field(None, description="ICD-10 or relevant code")
    ayush_terminology: Optional[str] = Field(None, description="Equivalent term in AYUSH system")
    confidence: Optional[float] = Field(None, description="Confidence score for this diagnosis")

class Prakriti(BaseModel):
    primary_dosha: Optional[str] = Field(None, description="Primary Dosha (Vata, Pitta, Kapha)")
    secondary_dosha: Optional[str] = Field(None, description="Secondary Dosha if any")
    assessment_notes: Optional[str] = Field(None, description="Basis for Prakriti assessment")

class Therapy(BaseModel):
    medicine: str = Field(..., description="Name of the medicine or therapy")
    dosage: Optional[str] = Field(None, description="Dosage instructions")
    duration: Optional[str] = Field(None, description="Duration of therapy")
    anupana: Optional[str] = Field(None, description="Vehicle/Medium for medicine intake (e.g., warm water, honey)")

class EHRDraft(BaseModel):
    demographics: Demographics = Field(default_factory=Demographics)
    presenting_complaints: List[PresentingComplaint] = Field(default_factory=list)
    clinical_findings: List[ClinicalFinding] = Field(default_factory=list)
    diagnosis: List[Diagnosis] = Field(default_factory=list)
    prakriti: Prakriti = Field(default_factory=Prakriti)
    comorbidities: List[str] = Field(default_factory=list, description="List of existing comorbidities")
    therapies: List[Therapy] = Field(default_factory=list)
    lifestyle_advice: List[str] = Field(default_factory=list, description="Dietary and lifestyle recommendations")
    follow_up: Optional[str] = Field(None, description="Follow-up instructions")

class ConfidenceScores(BaseModel):
    overall: float = Field(0.0, description="Overall confidence in the extraction")
    fields: Dict[str, float] = Field(default_factory=dict, description="Confidence score per field")

class ClinicalResponse(BaseModel):
    ehr_draft: EHRDraft = Field(default_factory=EHRDraft)
    confidence_scores: ConfidenceScores = Field(default_factory=ConfidenceScores)
    clarifications_required: List[str] = Field(default_factory=list, description="List of questions to clarify missing/ambiguous info")

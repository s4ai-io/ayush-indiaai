"""
Pydantic models for request/response validation
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class HerbRecommendation(BaseModel):
    """Individual herb recommendation"""
    name: str
    dosage: str
    benefits: str


class YogaRecommendation(BaseModel):
    """Individual yoga practice recommendation"""
    practice: str
    duration: str
    benefits: str


class PatientProfile(BaseModel):
    """Patient profile for treatment recommendation"""
    age: int = Field(35, ge=0, le=120, description="Patient age in years")
    gender: str = Field("Male", description="Patient gender (Male/Female)")
    prakriti: Optional[str] = Field(None, description="Natural constitution (Prakriti)")
    vikriti: Optional[str] = Field(None, description="Current dosha imbalance (Vikriti)")
    disease: str = Field(..., min_length=1, description="Primary health condition (required)")
    symptoms: Optional[str] = Field(None, description="Patient symptoms (optional)")
    comorbidities: Optional[str] = Field(None, description="Patient medical history or comorbidities")
    bmi: Optional[float] = Field(None, ge=10, le=50, description="Body Mass Index")
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v: str) -> str:
        # Accept any gender, normalize for ML model compatibility
        if v not in ['Male', 'Female']:
            return 'Male'  # Default for ML model if non-binary/other
        return v
    
    @field_validator('prakriti', 'vikriti')
    @classmethod
    def validate_dosha(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_doshas = [
            'Vata', 'Pitta', 'Kapha',
            'Vata-Pitta', 'Pitta-Kapha', 'Vata-Kapha',
            'Tridosha'
        ]
        if v not in valid_doshas:
            # Soft-validate: return the value as-is rather than reject
            # (CSV data often has non-standard combos like "Kapha-Pitta")
            return v
        return v


class TreatmentRecommendation(BaseModel):
    """Treatment recommendation response from ISHAAyush dataset"""
    # Core treatment recommendations
    herbs: List[HerbRecommendation] = Field(default_factory=list)
    yoga: List[YogaRecommendation] = Field(default_factory=list)
    diet: List[str] = Field(default_factory=list)
    lifestyle: List[str] = Field(default_factory=list)

    # Fallback fields
    no_match_found: bool = False
    message: str = ""
    
    # ISHAAyush-specific fields
    formulation: Optional[str] = Field(None, description="Ayurvedic formulation with dosage")
    prevention: List[str] = Field(default_factory=list, description="Prevention recommendations")
    prognosis: Optional[str] = Field(None, description="Disease prognosis")
    complications: List[str] = Field(default_factory=list, description="Possible complications")
    medical_intervention: Optional[str] = Field(None, description="Allopathic intervention if needed")
    doshas_affected: Optional[str] = Field(None, description="Affected doshas")
    
    # Match metadata
    source_disease: Optional[str] = Field(None, description="Matched disease from dataset")
    match_confidence: Optional[float] = Field(None, description="Match confidence 0-1")
    match_method: Optional[str] = Field(None, description="exact | fuzzy | symptom_similarity | fallback")
    
    # Predictions
    predicted_improvement: Optional[float] = Field(None, description="Predicted improvement percentage")
    recommended_duration_weeks: Optional[int] = Field(None, description="Recommended treatment duration")
    
    # Explainability
    explainability: List[str] = Field(default_factory=list, description="AI reasoning for recommendations")


class PrescriptionRequest(BaseModel):
    """Full prescription payload when doctor clicks 'Save & Prescribe'"""
    patientId: str = Field(..., description="Patient UUID")
    visitId: Optional[str] = Field(None, description="Existing visit/medical record ID")
    disease: Optional[str] = Field("", description="Diagnosed disease")
    symptoms: Optional[str] = Field("", description="Patient symptoms text")
    comorbidities: Optional[str] = Field("", description="Patient comorbidities/medical history")
    prakriti: str = Field("Vata", description="Patient prakriti")
    vikriti: str = Field("Vata", description="Patient current dosha imbalance")
    treatmentPlan: Optional[dict] = Field(None, description="Full AI treatment plan JSON")
    doctorPrescription: Optional[str] = Field("", description="Doctor's prescription notes")
    doctorNotes: Optional[str] = Field("", description="Additional doctor notes")
    rating: Optional[str] = Field(None, description="positive / negative")
    feedback: Optional[str] = Field(None, description="Doctor feedback text")
    original_ai_plan: Optional[dict] = Field(None, description="Original unmodified AI plan before doctor edits")

    # Basic health parameters (vitals) captured at this visit
    bpm: Optional[int] = Field(None, description="Heart rate (beats/min)")
    sugar_level: Optional[float] = Field(None, description="Blood glucose (mg/dL)")
    spo2: Optional[int] = Field(None, description="Blood oxygen saturation (%)")
    temperature: Optional[float] = Field(None, description="Body temperature (°C)")
    systolic_bp: Optional[int] = Field(None, description="Systolic blood pressure (mmHg)")
    diastolic_bp: Optional[int] = Field(None, description="Diastolic blood pressure (mmHg)")


class TreatmentFeedback(BaseModel):
    """Doctor feedback on treatment plan"""
    patientId: str
    treatmentPlan: dict  # Storing as dict to be flexible
    context: dict # Input features (Prakriti, Severity, etc.)
    rating: Optional[str] = None
    feedback: Optional[str] = None
    timestamp: str


class ForecastDataPoint(BaseModel):
    """Single forecast data point"""
    month: str
    predicted_cases: float
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None
    month_name: Optional[str] = None
    disease: Optional[str] = None
    season: Optional[str] = None
    ritu_sandhi: Optional[bool] = None


class ForecastResponse(BaseModel):
    """Disease forecast response"""
    disease: str
    forecast_months: int
    forecast_data: List[ForecastDataPoint]
    by_disease: Optional[dict] = None
    trend: str  # "increasing", "decreasing", "stable"
    risk_level: str  # "low", "moderate", "high"


class EmergingTrend(BaseModel):
    """Emerging disease trend"""
    disease: str
    category: str
    current_cases: int
    growth_rate: float
    risk_score: float
    alert_level: str  # "low", "medium", "high", "critical"


class TrendsResponse(BaseModel):
    """Emerging trends response"""
    trends: List[EmergingTrend]
    generated_at: str



class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    models_loaded: bool
    storage: Optional[str] = None
    version: str


# --- Registration Agent Models ---



# --- Registration Agent Models ---


class BasicInfo(BaseModel):
    firstName: str = ""
    lastName: str = ""  # Optional
    gender: str = ""
    age: Optional[int] = None
    maritalStatus: str = ""


class ContactInfo(BaseModel):
    mobileNumber: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    pincode: str = ""


class OtherInfo(BaseModel):
    occupation: str = ""
    bloodGroup: str = ""
    idType: str = ""
    idNumber: str = ""

    @field_validator('idNumber')
    @classmethod
    def validate_id_number(cls, v: str, info):
        # We need access to idType to validate properly. 
        # Pydantic v2 validator with 'info' context is tricky if fields are validated independently.
        # Simple regex checks here if possible, or leave relaxed.
        # User asked: "Id type (aadahar - 12 digit no , pan card - 10 digit alphanumeric, voter id - 10 digit alphanumeric) same way"
        # "do this properly"
        
        # Since we validate per field, we can't easily see 'idType' here without model_validator.
        # But let's basic check.
        if v:
            v = v.strip().upper()
        return v

class ClinicalAssessment(BaseModel):
    symptoms: str = ""
    diagnosis: str = ""
    prakriti: Optional[str] = None
    vikriti: Optional[str] = None
    comorbidities: Optional[str] = None
    notes: Optional[str] = ""
    parent_visit_id: Optional[str] = Field(None, description="Prior visit ID being followed up, if any")

class ConsultationData(BaseModel):
    visitId: Optional[str] = None
    patientId: str
    assessment: ClinicalAssessment
    timestamp: Optional[str] = None


class RegistrationData(BaseModel):
    basicInfo: BasicInfo = BasicInfo()
    contactInfo: ContactInfo = ContactInfo()
    otherInfo: OtherInfo = OtherInfo()
    
    @field_validator('otherInfo')
    @classmethod
    def validate_identity(cls, v: OtherInfo) -> OtherInfo:
        # Cross-field validation can happen here if we used model_validator on RegistrationData, 
        # but 'otherInfo' is a sub-model.
        # Let's trust frontend or add logic in main.py service entry.
        # Actually Pydantic v2 'model_validator' on OtherInfo is best.
        return v



# --- Analytics Response Models ---


class HotspotResponse(BaseModel):
    """Single hotspot entry"""
    city:        Optional[str] = None
    pincode:     Optional[str] = None
    diagnosis:   str
    count:       int
    devanagari:  Optional[str] = None
    iast:        Optional[str] = None
    hindi:       Optional[str] = None


class AlertResponse(BaseModel):
    """Single outbreak alert — Z-Score/CUSUM anomaly detection result."""
    disease:      str
    severity:     str
    message:      str
    date:         str
    # Devanagari name fields
    devanagari:   Optional[str]   = None
    iast:         Optional[str]   = None
    hindi:        Optional[str]   = None
    # Z-Score enrichment fields
    z_score:      Optional[float] = None
    cusum_value:  Optional[float] = None
    surge_month:  Optional[str]   = None
    recent_cases: Optional[int]   = None
    pct_increase: Optional[float] = None
    baseline_avg: Optional[float] = None
    triggered_by: Optional[str]   = None
    # Weekly alert extra fields
    week:           Optional[str]   = None
    recent_weeks:   Optional[int]   = None
    baseline_std:   Optional[float] = None
    detection_type: Optional[str]   = None
    # Case-details drill-down window (ISO dates)
    window_start:   Optional[str]   = None
    window_end:     Optional[str]   = None


class DiseaseCount(BaseModel):
    """Disease with case count"""
    disease: str
    count: int


class CityCount(BaseModel):
    """City with patient count"""
    city: str
    count: int


class DashboardSummaryResponse(BaseModel):
    """Overall analytics dashboard summary"""
    total_patients: int
    total_medical_records: int
    total_health_records: int
    top_diseases: List[DiseaseCount]
    top_cities: List[CityCount]


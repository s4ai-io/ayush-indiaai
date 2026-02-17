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
    age: int = Field(..., ge=0, le=120, description="Patient age in years")
    gender: str = Field(..., description="Patient gender (Male/Female)")
    prakriti: str = Field(..., description="Natural constitution (Prakriti)")
    vikriti: str = Field(..., description="Current dosha imbalance (Vikriti)")
    disease: str = Field(..., description="Primary health condition")
    severity: int = Field(..., ge=1, le=10, description="Condition severity (1-10)")
    bmi: Optional[float] = Field(None, ge=10, le=50, description="Body Mass Index")
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v: str) -> str:
        if v not in ['Male', 'Female']:
            raise ValueError('Gender must be Male or Female')
        return v
    
    @field_validator('prakriti', 'vikriti')
    @classmethod
    def validate_dosha(cls, v: str) -> str:
        valid_doshas = [
            'Vata', 'Pitta', 'Kapha',
            'Vata-Pitta', 'Pitta-Kapha', 'Vata-Kapha',
            'Tridosha'
        ]
        if v not in valid_doshas:
            raise ValueError(f'Dosha must be one of: {", ".join(valid_doshas)}')
        return v


class TreatmentRecommendation(BaseModel):
    """Treatment recommendation response"""
    herbs: List[HerbRecommendation]
    yoga: List[YogaRecommendation]
    diet: List[str]
    lifestyle: List[str]
    predicted_improvement: Optional[float] = Field(None, description="Predicted improvement percentage")
    recommended_duration_weeks: Optional[int] = Field(None, description="Recommended treatment duration")
    cluster_id: Optional[int] = Field(None, description="Patient cluster ID")
    explainability: List[str] = Field(default_factory=list, description="Reasons for recommendations")


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


class ForecastResponse(BaseModel):
    """Disease forecast response"""
    disease: str
    forecast_months: int
    forecast_data: List[ForecastDataPoint]
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
    version: str


# --- Registration Agent Models ---


class BasicInfo(BaseModel):
    firstName: str = ""
    lastName: str = ""
    gender: str = ""
    dateOfBirth: str = ""
    onlyYearOfBirth: bool = False
    relationshipType: str = ""
    relationName: str = ""
    nationality: str = "Indian"
    maritalStatus: str = ""
    abhaId: str = ""
    insuranceProvider: str = ""

class ContactInfo(BaseModel):
    mobileNumber: str = ""
    emailId: str = ""
    correspondenceAddress: str = ""
    correspondenceCountry: str = "India"
    correspondenceState: str = ""
    correspondenceCity: str = ""
    correspondencePincode: str = ""
    isPermanentSame: bool = False
    permanentAddress: str = ""
    permanentCountry: str = "India"
    permanentState: str = ""
    permanentCity: str = ""
    permanentPincode: str = ""
    emergencyContactName: str = ""
    emergencyContactNumber: str = ""

class OtherInfo(BaseModel):
    qualification: str = ""
    occupation: str = ""
    bloodGroup: str = ""
    idType: str = ""
    idNumber: str = ""

class RegistrationData(BaseModel):
    basicInfo: BasicInfo = BasicInfo()
    contactInfo: ContactInfo = ContactInfo()
    otherInfo: OtherInfo = OtherInfo()

"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Request: patient triage input ───────────────────────────────────────────
class TriageRequest(BaseModel):
    age: int = Field(..., ge=0, le=120)
    sex: str = Field(..., pattern="^[MF]$")
    chief_complaint: Optional[str] = Field(None, max_length=500)
    symptoms: list[str] = Field(default_factory=list)
    heart_rate: Optional[int] = Field(None, ge=0, le=300)
    bp_systolic: Optional[int] = Field(None, ge=0, le=300)
    bp_diastolic: Optional[int] = Field(None, ge=0, le=200)
    respiratory_rate: Optional[int] = Field(None, ge=0, le=80)
    spo2: Optional[float] = Field(None, ge=0, le=100)
    temperature: Optional[float] = Field(None, ge=20.0, le=45.0)
    pain_score: Optional[int] = Field(None, ge=0, le=10)
    level_of_consciousness: str = Field(default="alert")
    medical_history: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    is_pregnant: bool = False
    is_postpartum: bool = False

    model_config = {
        "json_schema_extra": {
            "example": {
                "age": 54,
                "sex": "M",
                "chief_complaint": "chest pain for 1 hour",
                "symptoms": ["chest pain", "shortness of breath", "diaphoresis"],
                "heart_rate": 118,
                "bp_systolic": 90,
                "bp_diastolic": 60,
                "respiratory_rate": 24,
                "spo2": 89.0,
                "temperature": 38.2,
                "pain_score": 8,
                "level_of_consciousness": "alert",
                "medical_history": ["hypertension", "diabetes"],
                "medications": ["metformin"],
                "allergies": [],
                "is_pregnant": False,
                "is_postpartum": False,
            }
        }
    }


# ── Response: triage result ─────────────────────────────────────────────────
class TriageResponse(BaseModel):
    id: Optional[int] = None
    esi_level: int
    risk: str
    reasons: list[str]
    warnings: list[str]
    recommendation: str


# ── Clinician override ──────────────────────────────────────────────────────
class ClinicianOverride(BaseModel):
    clinician_esi_level: int = Field(..., ge=1, le=5)
    clinician_notes: Optional[str] = None


# ── Outcome record ──────────────────────────────────────────────────────────
class OutcomeRecord(BaseModel):
    outcome: str  # "discharged", "admitted", "icu", "transferred", "deceased"
    outcome_notes: Optional[str] = None


# ── Database record returned by API ─────────────────────────────────────────
class TriageRecord(BaseModel):
    id: int
    created_at: datetime
    age: int
    sex: str
    chief_complaint: Optional[str]
    heart_rate: Optional[int]
    bp_systolic: Optional[int]
    bp_diastolic: Optional[int]
    respiratory_rate: Optional[int]
    spo2: Optional[float]
    temperature: Optional[float]
    pain_score: Optional[int]
    level_of_consciousness: str
    symptoms: list[str]
    medical_history: list[str]
    medications: list[str]
    allergies: list[str]
    ai_esi_level: Optional[int]
    ai_risk: Optional[str]
    ai_reasons: list[str]
    ai_warnings: list[str]
    ai_recommendation: Optional[str]
    clinician_esi_level: Optional[int]
    clinician_notes: Optional[str]
    outcome: Optional[str]
    outcome_notes: Optional[str]

    model_config = {"from_attributes": True}


# ── Dashboard metrics ───────────────────────────────────────────────────────
class DashboardMetrics(BaseModel):
    total_assessments: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    ai_clinician_agreement: float  # percentage
    under_triage_rate: float       # percentage (did AI flag higher than clinician?)
    over_triage_rate: float        # percentage (did AI flag higher than outcome required?)

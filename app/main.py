"""
FastAPI main application — ED Triage AI Assistant.
"""

import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import init_db, get_session, TriageAssessment, ESILevel
from app.triage import TriageEngine, PatientData
from app.models import (
    TriageRequest, TriageResponse, TriageRecord,
    ClinicianOverride, OutcomeRecord, DashboardMetrics
)

app = FastAPI(
    title="ED Triage AI Assistant",
    description="AI-powered triage decision support based on ESI v5 algorithm.",
    version="1.0.0",
)

# CORS — allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = TriageEngine()


# ── Startup ─────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    await init_db()


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "ed-triage-ai", "version": "1.0.0"}


# ── POST /triage — main triage endpoint ──────────────────────────────────────
@app.post("/triage", response_model=TriageResponse)
async def assess_triage(
    request: TriageRequest,
    session: AsyncSession = Depends(get_session),
):
    """Run the ESI-based triage rule engine on patient data."""

    # Build PatientData for the rule engine
    patient = PatientData(
        age=request.age,
        sex=request.sex,
        chief_complaint=request.chief_complaint or "",
        symptoms=request.symptoms,
        heart_rate=request.heart_rate,
        bp_systolic=request.bp_systolic,
        bp_diastolic=request.bp_diastolic,
        respiratory_rate=request.respiratory_rate,
        spo2=request.spo2,
        temperature=request.temperature,
        pain_score=request.pain_score,
        level_of_consciousness=request.level_of_consciousness,
        medical_history=request.medical_history,
        medications=request.medications,
        allergies=request.allergies,
        is_pregnant=request.is_pregnant,
        is_postpartum=request.is_postpartum,
        is_infant=request.age < 1,
        is_toddler=1 <= request.age < 3,
    )

    # Run the triage engine
    result = engine.assess(patient)

    # Persist to database
    record = TriageAssessment(
        # Demographics
        age=request.age,
        sex=request.sex,
        chief_complaint=request.chief_complaint,
        # Vitals
        heart_rate=request.heart_rate,
        bp_systolic=request.bp_systolic,
        bp_diastolic=request.bp_diastolic,
        respiratory_rate=request.respiratory_rate,
        spo2=request.spo2,
        temperature=request.temperature,
        pain_score=request.pain_score,
        level_of_consciousness=request.level_of_consciousness,
        # Flags
        is_pregnant=request.is_pregnant,
        is_postpartum=request.is_postpartum,
        # Lists as JSON strings
        medical_history=json.dumps(request.medical_history),
        medications=json.dumps(request.medications),
        allergies=json.dumps(request.allergies),
        symptoms=json.dumps(request.symptoms),
        # AI output
        ai_esi_level=result.esi_level.value,
        ai_risk=result.risk,
        ai_reasons=json.dumps(result.reasons),
        ai_warnings=json.dumps(result.warnings),
        ai_recommendation=result.recommendation,
    )

    session.add(record)
    await session.commit()
    await session.refresh(record)

    return TriageResponse(
        id=record.id,
        esi_level=result.esi_level.value,
        risk=result.risk,
        reasons=result.reasons,
        warnings=result.warnings,
        recommendation=result.recommendation,
    )


# ── GET /assessments — list all triage records ───────────────────────────────
@app.get("/assessments", response_model=list[TriageRecord])
async def list_assessments(
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    """Return paginated list of triage assessments."""
    stmt = select(TriageAssessment).order_by(TriageAssessment.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    records = result.scalars().all()

    def _deserialize(record: TriageAssessment) -> dict:
        return {
            "id": record.id,
            "created_at": record.created_at,
            "age": record.age,
            "sex": record.sex,
            "chief_complaint": record.chief_complaint,
            "heart_rate": record.heart_rate,
            "bp_systolic": record.bp_systolic,
            "bp_diastolic": record.bp_diastolic,
            "respiratory_rate": record.respiratory_rate,
            "spo2": record.spo2,
            "temperature": record.temperature,
            "pain_score": record.pain_score,
            "level_of_consciousness": record.level_of_consciousness,
            "symptoms": json.loads(record.symptoms or "[]"),
            "medical_history": json.loads(record.medical_history or "[]"),
            "medications": json.loads(record.medications or "[]"),
            "allergies": json.loads(record.allergies or "[]"),
            "ai_esi_level": record.ai_esi_level,
            "ai_risk": record.ai_risk,
            "ai_reasons": json.loads(record.ai_reasons or "[]"),
            "ai_warnings": json.loads(record.ai_warnings or "[]"),
            "ai_recommendation": record.ai_recommendation,
            "clinician_esi_level": record.clinician_esi_level,
            "clinician_notes": record.clinician_notes,
            "outcome": record.outcome,
            "outcome_notes": record.outcome_notes,
        }

    return [TriageRecord(**_deserialize(r)) for r in records]


# ── GET /assessments/{id} — single record ────────────────────────────────────
@app.get("/assessments/{assessment_id}", response_model=TriageRecord)
async def get_assessment(
    assessment_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Return a single triage assessment by ID."""
    record = await session.get(TriageAssessment, assessment_id)
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found")

    def _deserialize(r: TriageAssessment) -> dict:
        return {
            "id": r.id,
            "created_at": r.created_at,
            "age": r.age,
            "sex": r.sex,
            "chief_complaint": r.chief_complaint,
            "heart_rate": r.heart_rate,
            "bp_systolic": r.bp_systolic,
            "bp_diastolic": r.bp_diastolic,
            "respiratory_rate": r.respiratory_rate,
            "spo2": r.spo2,
            "temperature": r.temperature,
            "pain_score": r.pain_score,
            "level_of_consciousness": r.level_of_consciousness,
            "symptoms": json.loads(r.symptoms or "[]"),
            "medical_history": json.loads(r.medical_history or "[]"),
            "medications": json.loads(r.medications or "[]"),
            "allergies": json.loads(r.allergies or "[]"),
            "ai_esi_level": r.ai_esi_level,
            "ai_risk": r.ai_risk,
            "ai_reasons": json.loads(r.ai_reasons or "[]"),
            "ai_warnings": json.loads(r.ai_warnings or "[]"),
            "ai_recommendation": r.ai_recommendation,
            "clinician_esi_level": r.clinician_esi_level,
            "clinician_notes": r.clinician_notes,
            "outcome": r.outcome,
            "outcome_notes": r.outcome_notes,
        }

    return TriageRecord(**_deserialize(record))


# ── POST /assessments/{id}/override — clinician override ─────────────────────
@app.post("/assessments/{assessment_id}/override")
async def clinician_override(
    assessment_id: int,
    override: ClinicianOverride,
    session: AsyncSession = Depends(get_session),
):
    """Allow clinician to override or confirm AI triage level."""
    record = await session.get(TriageAssessment, assessment_id)
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found")

    record.clinician_esi_level = override.clinician_esi_level
    record.clinician_notes = override.clinician_notes
    await session.commit()
    await session.refresh(record)

    return {"message": "Override recorded", "id": record.id,
            "clinician_esi_level": record.clinician_esi_level}


# ── POST /assessments/{id}/outcome — record patient outcome ──────────────────
@app.post("/assessments/{assessment_id}/outcome")
async def record_outcome(
    assessment_id: int,
    outcome: OutcomeRecord,
    session: AsyncSession = Depends(get_session),
):
    """Record the actual patient outcome (for measuring AI accuracy)."""
    record = await session.get(TriageAssessment, assessment_id)
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found")

    record.outcome = outcome.outcome
    record.outcome_notes = outcome.outcome_notes
    await session.commit()
    await session.refresh(record)

    return {"message": "Outcome recorded", "id": record.id, "outcome": record.outcome}


# ── GET /dashboard — metrics for monitoring ─────────────────────────────────
@app.get("/dashboard", response_model=DashboardMetrics)
async def dashboard(session: AsyncSession = Depends(get_session)):
    """Return aggregate metrics for the triage dashboard."""

    total_result = await session.execute(select(func.count()).select_from(TriageAssessment))
    total_assessments = total_result.scalar() or 0

    # Count by risk level
    high_result = await session.execute(
        select(func.count()).select_from(TriageAssessment).where(TriageAssessment.ai_risk == "HIGH")
    )
    med_result = await session.execute(
        select(func.count()).select_from(TriageAssessment).where(TriageAssessment.ai_risk == "MEDIUM")
    )
    low_result = await session.execute(
        select(func.count()).select_from(TriageAssessment).where(TriageAssessment.ai_risk == "LOW")
    )

    high_count = high_result.scalar() or 0
    med_count = med_result.scalar() or 0
    low_count = low_result.scalar() or 0

    # Agreement rate between AI and clinician
    agreement_result = await session.execute(
        select(func.count()).select_from(TriageAssessment)
        .where(TriageAssessment.clinician_esi_level.is_not(None))
        .where(TriageAssessment.ai_esi_level == TriageAssessment.clinician_esi_level)
    )
    clinician_total = await session.execute(
        select(func.count()).select_from(TriageAssessment)
        .where(TriageAssessment.clinician_esi_level.is_not(None))
    )
    agreement_count = agreement_result.scalar() or 0
    clinician_count = clinician_total.scalar() or 0
    agreement_pct = (agreement_count / clinician_count * 100) if clinician_count > 0 else 0.0

    # Under-triage: AI rated lower than clinician (AI missed risk)
    under_result = await session.execute(
        select(func.count()).select_from(TriageAssessment)
        .where(TriageAssessment.clinician_esi_level.is_not(None))
        .where(TriageAssessment.ai_esi_level > TriageAssessment.clinician_esi_level)
    )
    under_count = under_result.scalar() or 0
    under_triage_pct = (under_count / clinician_count * 100) if clinician_count > 0 else 0.0

    # Over-triage: AI rated higher than clinician (AI over-flagged)
    over_result = await session.execute(
        select(func.count()).select_from(TriageAssessment)
        .where(TriageAssessment.clinician_esi_level.is_not(None))
        .where(TriageAssessment.ai_esi_level < TriageAssessment.clinician_esi_level)
    )
    over_count = over_result.scalar() or 0
    over_triage_pct = (over_count / clinician_count * 100) if clinician_count > 0 else 0.0

    return DashboardMetrics(
        total_assessments=total_assessments,
        high_risk_count=high_count,
        medium_risk_count=med_count,
        low_risk_count=low_count,
        ai_clinician_agreement=round(agreement_pct, 1),
        under_triage_rate=round(under_triage_pct, 1),
        over_triage_rate=round(over_triage_pct, 1),
    )

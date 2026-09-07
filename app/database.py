"""
Database configuration and models.
Uses SQLAlchemy with async PostgreSQL support.
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, Text, DateTime, Boolean, Enum as SQLEnum
from datetime import datetime
from enum import IntEnum

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./triage.db")


# ── Shared enums ────────────────────────────────────────────────────────────
class ESILevel(IntEnum):
    IMMEDIATE = 1
    URGENT = 2
    LESS_URGENT = 3
    NON_URGENT = 4
    MINIMAL = 5


class RiskLevel(str):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ── SQLAlchemy base ─────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── TriageAssessment model ──────────────────────────────────────────────────
class TriageAssessment(Base):
    __tablename__ = "triage_assessments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Demographics
    age: Mapped[int] = mapped_column(Integer)
    sex: Mapped[str] = mapped_column(String(1))
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Vitals
    heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bp_systolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bp_diastolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    respiratory_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spo2: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    pain_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    level_of_consciousness: Mapped[str] = mapped_column(String(20), default="alert")

    # Flags
    is_pregnant: Mapped[bool] = mapped_column(Boolean, default=False)
    is_postpartum: Mapped[bool] = mapped_column(Boolean, default=False)
    medical_history: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON string
    medications: Mapped[str | None] = mapped_column(Text, nullable=True)       # JSON string
    allergies: Mapped[str | None] = mapped_column(Text, nullable=True)         # JSON string
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)          # JSON string

    # AI output
    ai_esi_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_risk: Mapped[str | None] = mapped_column(String(10), nullable=True)
    ai_reasons: Mapped[str | None] = mapped_column(Text, nullable=True)        # JSON string
    ai_warnings: Mapped[str | None] = mapped_column(Text, nullable=True)       # JSON string
    ai_recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Clinician override
    clinician_esi_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clinician_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Outcome (filled after patient leaves)
    outcome: Mapped[str | None] = mapped_column(String(50), nullable=True)     # admitted, discharged, transferred, etc.
    outcome_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# ── Engine setup ────────────────────────────────────────────────────────────
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

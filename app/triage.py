"""
ED Triage Rule Engine
Based on ESI (Emergency Severity Index) v5 algorithm.
Extracted from: ESI Handbook, 5th Edition, Emergency Nurses Association.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import IntEnum


class ESILevel(IntEnum):
    IMMEDIATE = 1      # ESI 1 - Lifesaving intervention required
    URGENT = 2         # ESI 2 - High risk / Severe pain / AMS
    LESS_URGENT = 3    # ESI 3 - Stable, needs multiple resources
    NON_URGENT = 4     # ESI 4 - Stable, needs one resource
    MINIMAL = 5        # ESI 5 - Stable, no resources needed


@dataclass
class PatientData:
    age: int
    sex: str  # "M" or "F"
    chief_complaint: str = ""
    symptoms: list[str] = field(default_factory=list)
    heart_rate: Optional[int] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    respiratory_rate: Optional[int] = None
    spo2: Optional[float] = None
    temperature: Optional[float] = None  # Celsius
    pain_score: Optional[int] = None  # 0-10
    level_of_consciousness: str = "alert"  # alert, confused, lethargic, unresponsive
    medical_history: list[str] = field(default_factory=list)
    medications: list[str] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    is_pregnant: bool = False
    is_postpartum: bool = False
    is_infant: bool = False   # < 28 days
    is_toddler: bool = False  # 1-3 years


@dataclass
class TriageResult:
    esi_level: ESILevel
    risk: str  # "HIGH", "MEDIUM", "LOW"
    reasons: list[str]
    warnings: list[str]
    recommendation: str


class TriageEngine:

    # ── Adult vital-sign thresholds (≥ 18 years) ─────────────────────────
    # Decision Point D: High-Risk Vital Signs (p. 23-25, ESI Handbook)
    ADULT_HR_HIGH = 100
    ADULT_HR_LOW = 40
    ADULT_RR_HIGH = 20
    ADULT_RR_LOW = 12  # below 10 is explicit in ESI
    ADULT_SPO2_THRESHOLD = 92.0

    # ── Pediatric HR/RR thresholds ───────────────────────────────────────
    # Table 6-1 (p. 24, ESI Handbook)
    PED_HR_THRESHOLDS = {
        (0, 1): {"low": 90, "high": 190},       # < 1 month
        (1, 12): {"low": 90, "high": 180},      # 1-12 months
        (12, 36): {"low": 80, "high": 140},     # 1-3 years
        (36, 60): {"low": 65, "high": 120},     # 3-5 years
        (60, 144): {"low": 70, "high": 120},    # 5-12 years
        (144, 216): {"low": 60, "high": 100},   # 12-18 years
    }

    PED_RR_THRESHOLDS = {
        (0, 1): {"low": 35, "high": 60},
        (1, 12): {"low": 30, "high": 55},
        (12, 36): {"low": 22, "high": 40},
        (36, 60): {"low": 18, "high": 35},
        (60, 144): {"low": 16, "high": 30},
        (144, 216): {"low": 12, "high": 20},
    }

    def assess(self, p: PatientData) -> TriageResult:
        reasons: list[str] = []
        warnings: list[str] = []

        # ── Sex-based sanity guard ────────────────────────────────────────
        # Pregnancy flags are only valid for female patients
        if p.sex != "F":
            p.is_pregnant = False
            p.is_postpartum = False
            p.medical_history = [h for h in p.medical_history if h.lower() != "pregnancy"]

        # ══════════════════════════════════════════════════════════════════
        # DECISION POINT A: Lifesaving Intervention Required? → ESI 1
        # (p. 9-10, ESI Handbook)
        # ══════════════════════════════════════════════════════════════════
        if self._check_level1(p, reasons, warnings):
            return TriageResult(
                esi_level=ESILevel.IMMEDIATE,
                risk="HIGH",
                reasons=reasons,
                warnings=warnings,
                recommendation="IMMEDIATE — Lifesaving intervention required. "
                               "Do not delay. Activate resuscitation team.",
            )

        # ══════════════════════════════════════════════════════════════════
        # DECISION POINT B: High-Risk Situation? → ESI 2
        # (p. 11-18, ESI Handbook)
        # ══════════════════════════════════════════════════════════════════
        if self._check_level2(p, reasons, warnings):
            return TriageResult(
                esi_level=ESILevel.URGENT,
                risk="HIGH",
                reasons=reasons,
                warnings=warnings,
                recommendation="URGENT — High-risk presentation. Rapid assessment "
                               "and treatment required. Notify charge nurse.",
            )

        # ══════════════════════════════════════════════════════════════════
        # DECISION POINT D: High-Risk Vital Signs? → reassess to ESI 2
        # (p. 23-25, ESI Handbook)
        # ══════════════════════════════════════════════════════════════════
        vital_escalation = self._check_vital_signs(p, reasons, warnings)
        if vital_escalation:
            return TriageResult(
                esi_level=ESILevel.URGENT,
                risk="HIGH",
                reasons=reasons,
                warnings=warnings,
                recommendation="URGENT — Abnormal vital signs detected. "
                               "Reassess and consider up-triage.",
            )

        # ══════════════════════════════════════════════════════════════════
        # DECISION POINT C: Resource prediction → ESI 3, 4, or 5
        # (p. 19-22, ESI Handbook)
        # For our prototype, we use symptom complexity as a proxy for resources.
        # ══════════════════════════════════════════════════════════════════
        return self._check_resources(p, reasons, warnings)

    # ─────────────────────────────────────────────────────────────────────
    # DECISION POINT A
    # ─────────────────────────────────────────────────────────────────────
    def _check_level1(self, p: PatientData, reasons: list, warnings: list) -> bool:
        """Return True if patient needs immediate lifesaving intervention (ESI 1)."""

        # Unresponsive (AVPU P or U)
        if p.level_of_consciousness in ("unresponsive", "pain"):
            reasons.append("Unresponsive patient — immediate intervention required")
            return True

        # Apneic
        if p.respiratory_rate is not None and p.respiratory_rate == 0:
            reasons.append("Apneic — no respiratory effort")
            return True

        # SpO2 < 90% with respiratory compromise
        if p.spo2 is not None and p.spo2 < 90:
            # Check if this is NOT patient's normal (context from history)
            if not any("COPD" in h or "baseline" in h.lower() for h in p.medical_history):
                reasons.append(f"Severe hypoxemia: SpO2 {p.spo2}% < 90%")
                return True

        # Profound hypotension
        if p.bp_systolic is not None and p.bp_systolic < 80:
            reasons.append(f"Profound hypotension: BP {p.bp_systolic}/{p.bp_diastolic or '?'} mmHg")
            return True

        # Cardiac/pulmonary arrest indicators
        if p.heart_rate is not None and p.heart_rate == 0:
            reasons.append("No detectable pulse")
            return True

        # Severe bradycardia
        if p.heart_rate is not None and p.heart_rate < 40:
            reasons.append(f"Severe bradycardia: HR {p.heart_rate} bpm")
            return True

        # Severe tachycardia
        if p.heart_rate is not None and p.heart_rate > 180:
            reasons.append(f"Severe tachycardia: HR {p.heart_rate} bpm")
            return True

        # Hypoglycemia (cannot detect from vitals alone without glucose reading,
        # but AMS + diabetic = flag)
        if "diabetes" in " ".join(p.medical_history).lower() and p.level_of_consciousness in ("confused", "lethargic", "unresponsive"):
            warnings.append("Possible hypoglycemia — check blood glucose immediately")
            # Not automatic level 1 without glucose, but flag strongly

        return False

    # ─────────────────────────────────────────────────────────────────────
    # DECISION POINT B
    # ─────────────────────────────────────────────────────────────────────
    def _check_level2(self, p: PatientData, reasons: list, warnings: list) -> bool:
        """Return True if patient meets ESI Level 2 (high-risk) criteria."""

        symptom_lower = " ".join(p.symptoms).lower()
        history_lower = " ".join(p.medical_history).lower()

        # ── Altered Mental Status ────────────────────────────────────────
        if p.level_of_consciousness in ("confused", "lethargic", "disoriented"):
            reasons.append("New onset altered mental status (confused/lethargic/disoriented)")
            return True

        # ── Severe Pain / Distress (≥ 7/10) ──────────────────────────────
        if p.pain_score is not None and p.pain_score >= 7:
            # Distinguish systemic vs local pain
            systemic_keywords = ["abdomen", "abdominal", "chest", "flank", "head", "migraine"]
            if any(kw in symptom_lower for kw in systemic_keywords):
                reasons.append(f"Severe pain ({p.pain_score}/10) from systemic cause")
                return True
            else:
                # Localized pain (e.g., fracture) — still flag but may be level 3
                reasons.append(f"Severe pain ({p.pain_score}/10)")
                # Don't auto-return True; continue to resource assessment

        # ── Chest Pain ───────────────────────────────────────────────────
        if "chest pain" in symptom_lower:
            reasons.append("Active chest pain — suspicious for acute coronary syndrome")
            # If also unstable vitals → already caught in DP-A
            if p.level_of_consciousness != "alert":
                return True
            return True  # Chest pain alone = ESI 2 per guidelines

        # ── Stroke Signs ─────────────────────────────────────────────────
        stroke_keywords = ["face drooping", "arm weakness", "speech difficulty",
                           "slurred speech", "aphasia", "sudden weakness",
                           "sudden numbness", "sudden vision loss"]
        if any(kw in symptom_lower for kw in stroke_keywords):
            reasons.append("Signs of possible acute stroke — time-sensitive")
            return True

        # ── Severe Respiratory Distress ──────────────────────────────────
        resp_distress_keywords = ["shortness of breath", "difficulty breathing",
                                   "respiratory distress", "wheezing", "stridor"]
        if any(kw in symptom_lower for kw in resp_distress_keywords):
            reasons.append("Respiratory distress — potential deterioration")
            # If SpO2 also low → already caught in DP-A or DP-D
            return True

        # ── Suspected Sepsis / Immunocompromised + Fever ────────────────
        fever = p.temperature is not None and p.temperature >= 38.0
        immunocompromised = any(x in history_lower for x in
                                ["chemotherapy", "transplant", "hiv", "immunosuppressed",
                                 "steroid", "corticosteroid", "asplenia"])

        if fever and immunocompromised:
            reasons.append("Fever in immunocompromised patient — high risk for sepsis")
            return True

        # Sepsis suspicion from vitals
        if fever and p.heart_rate and p.heart_rate > 90 and p.respiratory_rate and p.respiratory_rate > 20:
            reasons.append("Fever + tachycardia + tachypnea — possible sepsis (qSOFA positive)")
            return True

        # ── Pregnancy / Postpartum Concerns ──────────────────────────────
        if (p.is_pregnant or p.is_postpartum):
            if p.bp_systolic and (p.bp_systolic < 90 or p.bp_systolic > 150):
                reasons.append(f"Abnormal BP in pregnant/postpartum patient: {p.bp_systolic} mmHg")
                return True
            if "chest pain" in symptom_lower or "shortness of breath" in symptom_lower:
                reasons.append("Cardiopulmonary symptoms in pregnant/postpartum patient")
                return True
            if "abdominal pain" in symptom_lower and "vaginal bleeding" in symptom_lower:
                reasons.append("Abdominal pain + vaginal bleeding in pregnancy — possible ectopic/miscarriage")
                return True
            if "heavy vaginal bleeding" in symptom_lower:
                reasons.append("Heavy vaginal bleeding postpartum — hemorrhagic risk")
                return True

        # ── Trauma ───────────────────────────────────────────────────────
        trauma_keywords = ["gunshot", "stab wound", "fall", "motor vehicle",
                           "mvc", "penetrating trauma"]
        if any(kw in symptom_lower for kw in trauma_keywords):
            reasons.append("Trauma mechanism — high risk for serious injury")
            if p.age > 55:
                reasons.append("Advanced age increases trauma severity risk")
            return True

        # ── Mental Health ────────────────────────────────────────────────
        mh_keywords = ["suicidal", "homicidal", "psychotic", "self-harm",
                        "overdose", "sexual assault"]
        if any(kw in symptom_lower for kw in mh_keywords):
            reasons.append("High-risk behavioral health presentation")
            return True

        # ── Ingestion / Overdose ─────────────────────────────────────────
        tox_keywords = ["overdose", "ingestion", "poisoning", "toxic"]
        if any(kw in symptom_lower for kw in tox_keywords):
            reasons.append("Toxic ingestion — time-sensitive evaluation needed")
            if p.level_of_consciousness in ("confused", "lethargic", "unresponsive"):
                return True
            return True

        # ── Testicular / Ovarian Torsion ─────────────────────────────────
        torsion_keywords = ["testicular pain", "scrotal pain", "ovarian",
                            "lower quadrant pain"]
        if any(kw in symptom_lower for kw in torsion_keywords):
            reasons.append("Possible torsion — time-sensitive, risk of organ loss")
            return True

        # ── Abdominal pain in elderly ────────────────────────────────────
        if "abdominal pain" in symptom_lower and p.age >= 65:
            reasons.append("Abdominal pain in elderly patient — high risk of serious pathology")
            return True

        return False

    # ─────────────────────────────────────────────────────────────────────
    # DECISION POINT D: High-Risk Vital Signs
    # ─────────────────────────────────────────────────────────────────────
    def _check_vital_signs(self, p: PatientData, reasons: list, warnings: list) -> bool:
        """Check vitals for high-risk values. Returns True if escalation to ESI 2 is warranted."""

        escalated = False

        # Get age-appropriate thresholds
        hr_low, hr_high = self._get_hr_range(p.age)
        rr_low, rr_high = self._get_rr_range(p.age)

        # Heart Rate
        if p.heart_rate:
            if p.heart_rate > hr_high:
                reasons.append(f"Tachycardia: HR {p.heart_rate} bpm (threshold >{hr_high} for age)")
                escalated = True
            elif p.heart_rate < hr_low:
                reasons.append(f"Bradycardia: HR {p.heart_rate} bpm (threshold <{hr_low} for age)")
                escalated = True

        # Respiratory Rate
        if p.respiratory_rate:
            if p.respiratory_rate > rr_high:
                reasons.append(f"Tachypnea: RR {p.respiratory_rate} (threshold >{rr_high} for age)")
                escalated = True
            elif p.respiratory_rate < rr_low:
                reasons.append(f"Bradypnea: RR {p.respiratory_rate} (threshold <{rr_low} for age)")
                escalated = True

        # SpO2 (adults)
        if p.spo2 is not None and p.age >= 18:
            if p.spo2 < self.ADULT_SPO2_THRESHOLD:
                reasons.append(f"Hypoxemia: SpO2 {p.spo2}% < {self.ADULT_SPO2_THRESHOLD}%")
                escalated = True

        # SpO2 (pediatric) — general threshold
        if p.spo2 is not None and p.age < 18 and p.spo2 < 92:
            reasons.append(f"Hypoxemia: SpO2 {p.spo2}% < 92%")
            escalated = True

        # Blood pressure (adults)
        if p.bp_systolic is not None and p.age >= 18:
            if p.bp_systolic < 90:
                reasons.append(f"Hypotension: BP {p.bp_systolic}/{p.bp_diastolic or '?'} mmHg")
                escalated = True

        # Pediatric temperature flags
        if p.temperature is not None:
            if p.age < 28 and p.temperature > 38.0:
                reasons.append("Infant <28 days with fever — high risk")
                escalated = True
            elif p.age < 90 and (p.temperature > 38.0 or p.temperature < 36.0):
                reasons.append(f"Temperature {p.temperature}°C in infant <90 days")
                escalated = True

        return escalated

    # ─────────────────────────────────────────────────────────────────────
    # DECISION POINT C: Resource prediction
    # ─────────────────────────────────────────────────────────────────────
    def _check_resources(self, p: PatientData, reasons: list, warnings: list) -> TriageResult:
        """Estimate resource needs and assign ESI 3, 4, or 5."""
        resource_count = 0

        # Labs needed
        lab_keywords = ["abnormal", "pain", "fever", "infection", "vomiting",
                        "diarrhea", "injury", "trauma", "laceration", "fracture",
                        "urinary", "respiratory", "cardiac", "dizzy", "weakness"]
        if any(kw in " ".join(p.symptoms).lower() for kw in lab_keywords):
            resource_count += 1

        # Imaging needed
        img_keywords = ["injury", "trauma", "fracture", "fall", "headache",
                        "abdominal pain", "chest pain", "back pain"]
        if any(kw in " ".join(p.symptoms).lower() for kw in img_keywords):
            resource_count += 1

        # IV fluids needed
        if p.temperature and p.temperature > 38.0:
            resource_count += 1
        if "vomiting" in " ".join(p.symptoms).lower():
            resource_count += 1

        # Procedure needed
        proc_keywords = ["laceration", "fracture", "dislocation"]
        if any(kw in " ".join(p.symptoms).lower() for kw in proc_keywords):
            resource_count += 1

        # Speciality consultation
        if any(kw in " ".join(p.symptoms).lower() for kw in ["eye", "ear", "psychiatric"]):
            resource_count += 1

        if resource_count >= 2:
            return TriageResult(
                esi_level=ESILevel.LESS_URGENT,
                risk="MEDIUM",
                reasons=reasons + [f"Estimated {resource_count} resource types needed"],
                warnings=warnings,
                recommendation="LESS URGENT — Stable patient, multiple resources expected. "
                               "Monitor while waiting.",
            )
        elif resource_count == 1:
            return TriageResult(
                esi_level=ESILevel.NON_URGENT,
                risk="LOW",
                reasons=reasons + ["One resource type expected"],
                warnings=warnings,
                recommendation="NON-URGENT — Stable patient, one resource expected. "
                               "Can wait for treatment area availability.",
            )
        else:
            return TriageResult(
                esi_level=ESILevel.MINIMAL,
                risk="LOW",
                reasons=reasons + ["No resources beyond history/exam expected"],
                warnings=warnings,
                recommendation="MINIMAL — Stable patient, no resources beyond exam expected. "
                               "Routine care.",
            )

    # ─────────────────────────────────────────────────────────────────────
    # Helper: age-appropriate vital sign ranges
    # ─────────────────────────────────────────────────────────────────────
    def _get_hr_range(self, age_months: int):
        """Return (low_threshold, high_threshold) for heart rate based on age."""
        for (lo, hi), vals in self.PED_HR_THRESHOLDS.items():
            if lo <= age_months < hi:
                return vals["low"], vals["high"]
        # Adult default
        return self.ADULT_HR_LOW, self.ADULT_HR_HIGH

    def _get_rr_range(self, age_months: int):
        """Return (low_threshold, high_threshold) for respiratory rate based on age."""
        for (lo, hi), vals in self.PED_RR_THRESHOLDS.items():
            if lo <= age_months < hi:
                return vals["low"], vals["high"]
        # Adult default
        return 12, 20  # adult normal RR: 12-20

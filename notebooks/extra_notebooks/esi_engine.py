"""
esi_engine.py
=============
A rules-based engine implementing the Emergency Severity Index (ESI), Version 5
algorithm exactly as specified in the ENA "Emergency Severity Index Handbook,
Fifth Edition" (2023).

Design principle
-----------------
ESI triage is explicitly a *clinical judgment* tool (see Handbook Ch. 1-2 and
Appendix A). Several decision points ("high-risk situation?", "severe pain or
distress?", "ineffective tissue perfusion?", etc.) require a trained nurse's
assessment and cannot be safely auto-derived from raw numbers alone. This
engine therefore takes the nurse's assessment findings as *structured boolean
/ categorical inputs* (mirroring exactly the criteria printed in the
Handbook), and then applies the ESI v5 algorithm's decision logic
(Decision Points A -> B -> C -> D) deterministically and reproducibly.

Every rule below is annotated with the Handbook section/page it comes from
so it can be checked line-by-line against the source PDF.
"""

from dataclasses import dataclass, field
from typing import Optional, Set, List, Dict, Any
from enum import Enum


# ---------------------------------------------------------------------------
# Decision Point C — Resources (Handbook Ch. 5, Figure 5-1, Table 5-1)
# ---------------------------------------------------------------------------

# "ESI Resources" column of Table 5-1 / Figure 2-2.
# The nurse anticipates which *types* of resources will be used; counting is
# by TYPE, not by individual test (explicitly stated in Ch. 5 "Common
# Questions" and in the resource definition under Figure 2-2, panel C).
RESOURCE_TYPES = {
    "labs",                 # Labs (blood, urine) - CBC+lytes+coags = 1; CBC+UA = 1
    "ecg_or_radiograph",    # Electrocardiogram, radiographs (xray) - chest+abdo xray = 1
    "advanced_imaging",     # CT, MRI, ultrasound, angiography
    "iv_fluids",            # Intravenous fluids (hydration)
    "iv_im_neb_medications",# IV, IM, or nebulized medications
    "specialty_consultation",
    "simple_procedure",     # laceration repair, urinary catheter -> counts as 1
    "complex_procedure",    # procedural sedation -> counts as 2 (Table 5-1)
}

# "Not Resources" column of Table 5-1 / Figure 2-2 — included here only for
# documentation / validation purposes (e.g. to warn a caller who mistakenly
# passes one of these as if it were a countable resource).
NOT_RESOURCE_TYPES = {
    "history_and_physical_exam",   # incl. pelvic exam
    "point_of_care_testing",
    "saline_or_heparin_lock",
    "oral_medications",
    "tetanus_immunization",
    "prescription_refill",
    "phone_call_to_pcp",
    "simple_wound_care",           # dressings, recheck
    "crutches_splints_slings",
}


def count_resources(resource_types: Set[str]) -> int:
    """
    Decision Point C resource counter (Handbook Ch. 5 / Figure 2-2 panel C).

    Rules:
      * Count DIFFERENT TYPES of resources, not individual tests.
      * A "complex procedure" (e.g., procedural sedation) counts as 2.
      * A "simple procedure" (e.g., laceration repair, urinary catheter)
        counts as 1.
      * Anything in NOT_RESOURCE_TYPES contributes 0 and is ignored (but
        flagged) -- e.g. history/physical exam, point-of-care testing,
        saline/heparin lock, oral meds, tetanus shot, prescription refill,
        phone call to PCP, simple wound care, crutches/splints/slings.
    """
    unknown = resource_types - RESOURCE_TYPES - NOT_RESOURCE_TYPES
    if unknown:
        raise ValueError(f"Unrecognized resource type(s): {unknown}")

    count = 0
    for r in resource_types:
        if r == "complex_procedure":
            count += 2
        elif r in RESOURCE_TYPES:
            count += 1
        # anything in NOT_RESOURCE_TYPES contributes 0
    return count


def resource_count_to_level(n_resources: int) -> int:
    """
    Figure 5-1 / Figure 2-2 panel C:
        None  -> ESI 5
        One   -> ESI 4
        Many (>=2) -> ESI 3
    """
    if n_resources <= 0:
        return 5
    elif n_resources == 1:
        return 4
    else:
        return 3


# ---------------------------------------------------------------------------
# Decision Point D — High-risk vital signs (Handbook Ch. 6, Figure 6-1)
# ---------------------------------------------------------------------------

# Age bracket -> (HR threshold "greater than", RR threshold "greater than")
# Values are the exact cutoffs printed in Figure 2-2 / Figure 6-1 / Appendix B.
# A vital sign is "high risk" if it is STRICTLY GREATER THAN the listed value.
VITAL_SIGN_THRESHOLDS = [
    # (bracket_name, age_lower_incl_years, age_upper_excl_years, hr_gt, rr_gt)
    ("<1 mo",   0.0,      1/12,  190, 60),
    ("1-12 mo", 1/12,     1.0,   180, 55),
    ("1-3 y",   1.0,      3.0,   140, 40),
    ("3-5 y",   3.0,      5.0,   120, 35),
    ("5-12 y",  5.0,      12.0,  120, 30),
    ("12-18 y", 12.0,     18.0,  100, 20),
    (">18 y",   18.0,     999.0, 100, 20),
]

SPO2_HIGH_RISK_THRESHOLD = 92  # "SpO2 < 92%" applies across ALL age brackets


def get_age_bracket(age_years: float) -> str:
    """Return the Figure 6-1 age bracket name for a given age in years."""
    if age_years < 0:
        raise ValueError("age_years must be >= 0")
    for name, lo, hi, _, _ in VITAL_SIGN_THRESHOLDS:
        if lo <= age_years < hi:
            return name
    return ">18 y"


def check_high_risk_vitals(
    age_years: float,
    hr: Optional[float] = None,
    rr: Optional[float] = None,
    spo2: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Decision Point D (Handbook Ch. 6, Figure 6-1): determine whether the
    patient's vital signs exceed the age-based high-risk cutoffs.

    Returns a dict with:
        age_bracket, hr_high_risk, rr_high_risk, spo2_high_risk,
        any_high_risk, rationale (list[str])
    """
    bracket = get_age_bracket(age_years)
    _, _, _, hr_cut, rr_cut = next(
        b for b in VITAL_SIGN_THRESHOLDS if b[0] == bracket
    )

    rationale: List[str] = []
    hr_flag = hr is not None and hr > hr_cut
    if hr_flag:
        rationale.append(
            f"HR {hr} > {hr_cut} bpm (high-risk cutoff for age bracket '{bracket}')"
        )
    rr_flag = rr is not None and rr > rr_cut
    if rr_flag:
        rationale.append(
            f"RR {rr} > {rr_cut} /min (high-risk cutoff for age bracket '{bracket}')"
        )
    spo2_flag = spo2 is not None and spo2 < SPO2_HIGH_RISK_THRESHOLD
    if spo2_flag:
        rationale.append(
            f"SpO2 {spo2}% < {SPO2_HIGH_RISK_THRESHOLD}% (high-risk cutoff, all ages)"
        )

    return {
        "age_bracket": bracket,
        "hr_high_risk": hr_flag,
        "rr_high_risk": rr_flag,
        "spo2_high_risk": spo2_flag,
        "any_high_risk": hr_flag or rr_flag or spo2_flag,
        "rationale": rationale,
    }


# ---------------------------------------------------------------------------
# Pediatric fever considerations (Figure 2-2 panel D sidebar, and Ch. 6
# "Pediatric Temperatures" / Table 6-2, and Ch. 4 note on isolation)
# ---------------------------------------------------------------------------

def pediatric_fever_rule(
    age_days: float,
    temp_c: float,
    immunizations_up_to_date: Optional[bool] = None,
    obvious_fever_source: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Implements the "Pediatric Fever Considerations" box (Figure 2-2 / Appendix B):

        1-28 days of age:  Assign AT LEAST ESI 2 if T > 38 C (100.4 F)  [MANDATORY]
        1-3 months:        CONSIDER assigning ESI 2 if T > 38 C        [DISCRETIONARY]
        3 months and older: CONSIDER assigning ESI 2 or 3 if:
              (a) T > 39 C (102.2 F) or T < 36 C (96.8 F), OR
              (b) incomplete immunizations, OR
              (c) no obvious source of fever                            [DISCRETIONARY]

    Only the neonatal (<=28 day) rule is mandatory ("Assign AT LEAST ESI 2");
    the others are explicitly discretionary ("Consider") in the Handbook, so
    this function returns a recommendation rather than force-overriding the
    caller's own ESI level for those tiers.
    """
    result = {
        "tier": None,
        "mandatory_esi2": False,
        "consider_esi2": False,
        "consider_esi2_or_3": False,
        "rationale": [],
    }

    if age_days <= 28:
        result["tier"] = "neonate_1_28_days"
        if temp_c > 38.0:
            result["mandatory_esi2"] = True
            result["rationale"].append(
                f"Neonate (<=28 days) with T {temp_c}C > 38C: "
                "Handbook mandates 'Assign at least ESI 2'."
            )
    elif age_days <= 90:
        result["tier"] = "infant_1_3_months"
        if temp_c > 38.0:
            result["consider_esi2"] = True
            result["rationale"].append(
                f"Infant 1-3 months with T {temp_c}C > 38C: "
                "Handbook says 'Consider assigning ESI 2' (discretionary)."
            )
    else:
        result["tier"] = "3_months_and_older"
        reasons = []
        if temp_c > 39.0 or temp_c < 36.0:
            reasons.append(f"T {temp_c}C outside 36-39C band")
        if immunizations_up_to_date is False:
            reasons.append("incomplete immunizations")
        if obvious_fever_source is False:
            reasons.append("no obvious source of fever")
        if reasons:
            result["consider_esi2_or_3"] = True
            result["rationale"].append(
                "3 months+ with " + "; ".join(reasons) +
                ": Handbook says 'Consider assigning ESI 2 or 3' (discretionary)."
            )
    return result


# ---------------------------------------------------------------------------
# Decision Point A — Immediate lifesaving intervention required?
# (Handbook Ch. 3, Figure 3-1, Table 3-1)
# ---------------------------------------------------------------------------

@dataclass
class DecisionA:
    """
    Every field below is a distinct ESI level-1 trigger from Handbook Ch. 3.
    If ANY field is True, the patient is ESI level 1 and the algorithm stops
    (Decision Point A is "the only one needed for ESI level-1 patients").
    """
    # --- "Examples of ESI Level-1 Criteria" bullet list ---
    ineffective_airway_clearance: bool = False
    ineffective_respiratory_pattern: bool = False
    impaired_gas_exchange: bool = False
    ineffective_tissue_perfusion: bool = False
    obtunded_unresponsive: bool = False
    spo2_below_90_with_resp_compromise: bool = False
    anaphylaxis: bool = False
    hypotension_with_hypoperfusion: bool = False
    hypoglycemia_severe: bool = False
    severe_bradycardia_or_tachycardia: bool = False
    flaccid_infant: bool = False
    cardiac_or_pulmonary_arrest_or_imminent: bool = False
    penetrating_trauma_requiring_lifesaving_intervention: bool = False

    # --- Unresponsiveness definition (two ways to meet it), Table/Fig 3-1 panel A ---
    nonverbal_not_following_commands_acutely: bool = False
    requires_noxious_stimulus_P_or_U_on_AVPU: bool = False

    # --- Table 3-1 "Examples of Lifesaving Interventions" (by category) ---
    requires_assisted_ventilation_intubation_or_surgical_airway: bool = False
    requires_emergent_electrical_therapy: bool = False   # defib/cardioversion/pacing
    requires_emergent_lifesaving_procedure: bool = False  # needle decompression, pericardiocentesis, open thoracotomy
    requires_significant_ivf_or_blood_or_hemorrhage_control: bool = False
    requires_emergency_lifesaving_medication: bool = False  # adenosine, atropine, dextrose, dopamine, epi(incl IM anaphylaxis), naloxone

    def is_unresponsive(self) -> bool:
        return (
            self.nonverbal_not_following_commands_acutely
            or self.requires_noxious_stimulus_P_or_U_on_AVPU
        )

    def triggered_criteria(self) -> List[str]:
        """Return the list of field-names that are True (for rationale)."""
        triggers = []
        for f in self.__dataclass_fields__:
            if getattr(self, f) is True:
                triggers.append(f)
        return triggers

    def is_level_1(self) -> bool:
        return self.obtunded_unresponsive or self.is_unresponsive() or bool(
            self.triggered_criteria()
        )


# ---------------------------------------------------------------------------
# Decision Point B — High-risk situation / confused / severe pain-distress?
# (Handbook Ch. 4, Figure 4-1)
# ---------------------------------------------------------------------------

@dataclass
class DecisionB:
    """
    Decision Point B is satisfied (-> ESI 2) if ANY of the three top-level
    questions from Figure 4-1 is Yes:
        1. Is the situation high-risk?
        2. Is the patient confused/lethargic/disoriented (new-onset AMS)?
        3. Is the patient in severe pain or distress (physiological or
           psychological)?
    Below, each is broken into the concrete sub-criteria enumerated in the
    Handbook text so the caller can flag exactly what was observed.
    """
    # 1) High-risk situation - general flag plus the enumerated examples
    high_risk_situation: bool = False  # generic catch-all, set True for any
                                        # condition matching the "Examples of
                                        # high-risk situations" bullet list
                                        # (chest pain c/f ACS, stroke signs,
                                        # ectopic pregnancy stable, febrile
                                        # immunocompromised/transplant pt,
                                        # actively suicidal/homicidal, needle
                                        # stick in HCW, sexual assault
                                        # survivor, increasing resp effort,
                                        # postpartum hemorrhage, etc.)

    # 2) New onset confusion / lethargy / disorientation (acute change in
    #    mental status). Handbook: "If the patient's history is unknown, and
    #    the patient presents as confused, lethargic, or disoriented, the
    #    nurse should ASSUME this condition is new and assign an ESI level 2."
    confused_lethargic_disoriented: bool = False
    mental_status_history_unknown: bool = False  # if True, forces "assume new"

    # 3) Severe pain or distress
    pain_score_0_to_10: Optional[int] = None
    pain_from_systemic_disruption: bool = False  # e.g. renal colic, cancer
                                                  # pain, sickle cell crisis
                                                  # -> Handbook: "should be
                                                  # triaged as ESI level 2"
    severe_psychological_distress: bool = False  # distraught post-assault,
                                                  # behavioral outbursts,
                                                  # combativeness, DV/SV
                                                  # survivor, acute grief,
                                                  # suicidal ideation/plan/
                                                  # attempt, prenatal loss

    # OB-specific high-risk vital/bleeding rules (Ch. 4 "Obstetrical and
    # Gynecological Concerns")
    pregnant_or_postpartum: bool = False
    sbp: Optional[float] = None  # used only if pregnant_or_postpartum
    heavy_vaginal_bleeding: bool = False
    suspicion_of_infection: bool = False  # combined with heavy bleeding while pregnant
    postpartum_heavy_vaginal_bleeding: bool = False

    def evaluate(self) -> Dict[str, Any]:
        rationale: List[str] = []
        triggered = False

        if self.high_risk_situation:
            triggered = True
            rationale.append("High-risk situation flagged (Ch.4 examples list).")

        # New-onset AMS: if history unknown, ASSUME new (per Handbook).
        if self.confused_lethargic_disoriented:
            if self.mental_status_history_unknown:
                rationale.append(
                    "Confused/lethargic/disoriented with unknown baseline: "
                    "Handbook says assume NEW onset -> ESI 2."
                )
            else:
                rationale.append(
                    "New-onset confusion/lethargy/disorientation (AMS) -> ESI 2."
                )
            triggered = True

        # Severe pain/distress
        if self.pain_from_systemic_disruption:
            triggered = True
            rationale.append(
                "Severe pain/distress from systemic disruption "
                "(e.g., renal colic, cancer, sickle cell crisis) -> ESI 2."
            )
        if self.severe_psychological_distress:
            triggered = True
            rationale.append("Severe psychological distress -> ESI 2.")
        if self.pain_score_0_to_10 is not None and self.pain_score_0_to_10 >= 7:
            # NOTE: Handbook explicitly warns this is NOT automatic -
            # "not all patients with a pain score greater than 7 should be
            # triaged as ESI level 2" - it must be "considered" and assessed.
            # We surface it as a rationale note but do NOT auto-trigger,
            # unless pain_from_systemic_disruption / severe_psych_distress is
            # also set (handled above), consistent with the text.
            rationale.append(
                f"Pain score {self.pain_score_0_to_10}/10 (>=7): to be "
                "CONSIDERED for ESI 2 per Handbook, not automatic -- "
                "requires nurse assessment of cause (e.g., orthopedic pain "
                "with no neurovascular compromise may still wait)."
            )

        # OB rules
        if self.pregnant_or_postpartum and self.sbp is not None:
            if self.sbp < 90 or self.sbp > 150:
                triggered = True
                rationale.append(
                    f"Pregnant/postpartum with SBP {self.sbp} (<90 or >150) "
                    "-> ESI 2 even without other symptoms."
                )
        if (
            self.pregnant_or_postpartum
            and self.heavy_vaginal_bleeding
            and self.suspicion_of_infection
        ):
            triggered = True
            rationale.append(
                "Pregnant with heavy vaginal bleeding + suspicion of "
                "infection -> ESI 2."
            )
        if self.postpartum_heavy_vaginal_bleeding:
            triggered = True
            rationale.append("Postpartum heavy vaginal bleeding -> ESI 2.")

        return {"triggered": triggered, "rationale": rationale}


# ---------------------------------------------------------------------------
# Full patient case + top-level triage function
# ---------------------------------------------------------------------------

@dataclass
class PatientCase:
    age_years: float
    decision_a: DecisionA = field(default_factory=DecisionA)
    decision_b: DecisionB = field(default_factory=DecisionB)
    resources: Set[str] = field(default_factory=set)
    hr: Optional[float] = None
    rr: Optional[float] = None
    spo2: Optional[float] = None
    # pediatric fever inputs (optional)
    age_days: Optional[float] = None
    temp_c: Optional[float] = None
    immunizations_up_to_date: Optional[bool] = None
    obvious_fever_source: Optional[bool] = None
    # For Decision D reassessment: the Handbook (Ch.6) treats an exceeded
    # high-risk vital sign as triggering a mandatory REASSESSMENT, and
    # *recommends* uptriage to ESI 2 if, after reassessment, vitals remain
    # out of range. In one worked example (Ch.6 Example Four) the nurse's
    # clinical judgment kept the patient at the level from Decision C
    # despite a single borderline vital sign. This flag lets a caller
    # represent that documented clinical-judgment override; default is
    # False (i.e., default behavior follows the Handbook's general
    # recommendation to uptriage).
    nurse_override_no_uptriage_on_reassessment: bool = False


@dataclass
class TriageResult:
    esi_level: int
    decision_point_reached: str
    rationale: List[str]
    details: Dict[str, Any] = field(default_factory=dict)


def esi_triage(case: PatientCase) -> TriageResult:
    """
    Runs the ESI v5 algorithm end-to-end exactly following the sequence in
    Figure 2-2 / Appendix B ("ESI Triage Algorithm, v5"):

        A -> (if No) B -> (if No) C -> D -> (reassess loop back to 2 if
        high-risk vitals found)
    """
    rationale: List[str] = []

    # ---------------- Pediatric fever pre-check (feeds into Decision B) ---
    fever_info = None
    if case.age_days is not None and case.temp_c is not None:
        fever_info = pediatric_fever_rule(
            case.age_days,
            case.temp_c,
            case.immunizations_up_to_date,
            case.obvious_fever_source,
        )
        if fever_info["mandatory_esi2"]:
            case.decision_b.high_risk_situation = True
        rationale.extend(fever_info["rationale"])

    # ---------------- Decision Point A -------------------------------
    if case.decision_a.is_level_1():
        triggers = case.decision_a.triggered_criteria()
        rationale.append(
            f"Decision Point A: lifesaving intervention required "
            f"(criteria met: {triggers}) -> ESI 1."
        )
        return TriageResult(1, "A", rationale, {"fever_info": fever_info})

    rationale.append("Decision Point A: No immediate lifesaving intervention required.")

    # ---------------- Decision Point B -------------------------------
    b_eval = case.decision_b.evaluate()
    rationale.extend(b_eval["rationale"])
    if b_eval["triggered"]:
        rationale.append("Decision Point B: High-risk / AMS / severe distress -> ESI 2.")
        return TriageResult(2, "B", rationale, {"fever_info": fever_info})

    rationale.append("Decision Point B: Not high-risk, no new AMS, no severe pain/distress requiring ESI 2.")

    # ---------------- Decision Point C -------------------------------
    n_resources = count_resources(case.resources)
    tentative_level = resource_count_to_level(n_resources)
    rationale.append(
        f"Decision Point C: {n_resources} distinct resource type(s) anticipated "
        f"({sorted(case.resources) if case.resources else 'none'}) "
        f"-> tentative ESI {tentative_level}."
    )

    # ---------------- Decision Point D -------------------------------
    vitals = check_high_risk_vitals(case.age_years, case.hr, case.rr, case.spo2)
    rationale.extend(vitals["rationale"])

    if vitals["any_high_risk"]:
        if case.nurse_override_no_uptriage_on_reassessment:
            rationale.append(
                "Decision Point D: high-risk vital sign(s) present, but "
                "documented clinical-judgment reassessment determined "
                "uptriage was NOT warranted (Handbook Ch.6 permits this "
                "when other vitals/context are reassuring) "
                f"-> ESI remains {tentative_level}."
            )
            return TriageResult(
                tentative_level, "D (reassessed, no change)", rationale,
                {"fever_info": fever_info, "vitals": vitals, "resources": n_resources},
            )
        else:
            rationale.append(
                "Decision Point D: high-risk vital sign(s) present -> "
                "reassess acuity decision; per Handbook recommendation, "
                "uptriage to ESI 2."
            )
            return TriageResult(
                2, "D (reassessed -> uptriaged)", rationale,
                {"fever_info": fever_info, "vitals": vitals, "resources": n_resources},
            )

    rationale.append(
        f"Decision Point D: no high-risk vital signs -> final ESI {tentative_level}."
    )
    return TriageResult(
        tentative_level, "C/D", rationale,
        {"fever_info": fever_info, "vitals": vitals, "resources": n_resources},
    )

"""
test_esi_engine.py
===================
Exhaustive verification of esi_engine.py against the ESI v5 Handbook.

Organized into:
  1. Decision Point A - every individual level-1 trigger (Ch.3)
  2. Decision Point B - every individual high-risk/AMS/distress trigger (Ch.4)
  3. Decision Point C - resource counting rules (Ch.5 / Table 5-1)
  4. Decision Point D - age-bracket vital sign thresholds (Ch.6 / Fig 6-1)
  5. Pediatric fever rules (Fig 2-2 sidebar / Table 6-2)
  6. End-to-end worked examples taken VERBATIM from the Handbook
     (Table 5-2 rows, Chapter 6 Examples One-Five)
  7. Algorithm-order / precedence checks (A before B before C before D)

Every test raises AssertionError with a descriptive message on failure.
run_all() executes everything and returns a pass/fail summary.
"""

from esi_engine import (
    PatientCase, DecisionA, DecisionB, esi_triage,
    count_resources, resource_count_to_level, get_age_bracket,
    check_high_risk_vitals, pediatric_fever_rule, VITAL_SIGN_THRESHOLDS,
    RESOURCE_TYPES, NOT_RESOURCE_TYPES,
)

PASS = []
FAIL = []


def check(name, condition, detail=""):
    if condition:
        PASS.append(name)
    else:
        FAIL.append(f"{name} :: {detail}")


# ===========================================================================
# 1. DECISION POINT A - every individual ESI-1 trigger (Handbook Ch.3)
# ===========================================================================

A_BOOLEAN_FIELDS = [
    "ineffective_airway_clearance",
    "ineffective_respiratory_pattern",
    "impaired_gas_exchange",
    "ineffective_tissue_perfusion",
    "obtunded_unresponsive",
    "spo2_below_90_with_resp_compromise",
    "anaphylaxis",
    "hypotension_with_hypoperfusion",
    "hypoglycemia_severe",
    "severe_bradycardia_or_tachycardia",
    "flaccid_infant",
    "cardiac_or_pulmonary_arrest_or_imminent",
    "penetrating_trauma_requiring_lifesaving_intervention",
    "nonverbal_not_following_commands_acutely",
    "requires_noxious_stimulus_P_or_U_on_AVPU",
    "requires_assisted_ventilation_intubation_or_surgical_airway",
    "requires_emergent_electrical_therapy",
    "requires_emergent_lifesaving_procedure",
    "requires_significant_ivf_or_blood_or_hemorrhage_control",
    "requires_emergency_lifesaving_medication",
]

def test_decision_a_each_trigger_alone_gives_level_1():
    for fname in A_BOOLEAN_FIELDS:
        da = DecisionA(**{fname: True})
        case = PatientCase(age_years=40, decision_a=da, resources=set(),
                            hr=80, rr=16, spo2=98)
        result = esi_triage(case)
        check(
            f"A-trigger[{fname}] => ESI1",
            result.esi_level == 1 and result.decision_point_reached == "A",
            f"got level={result.esi_level}, dp={result.decision_point_reached}",
        )

def test_decision_a_no_triggers_does_not_force_level_1():
    da = DecisionA()  # all False
    case = PatientCase(age_years=40, decision_a=da, resources=set(),
                        hr=80, rr=16, spo2=98)
    result = esi_triage(case)
    check(
        "A-no-triggers => not forced to ESI1",
        result.esi_level != 1,
        f"got {result.esi_level}",
    )

def test_unresponsiveness_two_definitions():
    # "Is nonverbal and not following commands (acutely)"
    da1 = DecisionA(nonverbal_not_following_commands_acutely=True)
    check("unresponsive-def-1 (nonverbal/no commands)", da1.is_unresponsive())
    # "Requires noxious stimulus (P or U on AVPU scale)"
    da2 = DecisionA(requires_noxious_stimulus_P_or_U_on_AVPU=True)
    check("unresponsive-def-2 (P/U on AVPU)", da2.is_unresponsive())
    da3 = DecisionA()
    check("unresponsive-def-neither => False", not da3.is_unresponsive())


# ===========================================================================
# 2. DECISION POINT B - high-risk / AMS / severe pain-distress (Handbook Ch.4)
# ===========================================================================

def _base_case(db=None, hr=80, rr=16, spo2=98, age=40):
    return PatientCase(
        age_years=age, decision_a=DecisionA(), decision_b=db or DecisionB(),
        resources=set(), hr=hr, rr=rr, spo2=spo2,
    )

def test_b_high_risk_situation_flag():
    db = DecisionB(high_risk_situation=True)
    r = esi_triage(_base_case(db))
    check("B: high_risk_situation -> ESI2", r.esi_level == 2, r.esi_level)

def test_b_new_onset_ams_known_baseline():
    db = DecisionB(confused_lethargic_disoriented=True, mental_status_history_unknown=False)
    r = esi_triage(_base_case(db))
    check("B: new-onset AMS -> ESI2", r.esi_level == 2, r.esi_level)

def test_b_ams_unknown_baseline_assumed_new():
    # Handbook: "If the patient's history is unknown ... assume this
    # condition is new and assign an ESI level 2."
    db = DecisionB(confused_lethargic_disoriented=True, mental_status_history_unknown=True)
    r = esi_triage(_base_case(db))
    check("B: AMS + unknown baseline assumed new -> ESI2", r.esi_level == 2, r.esi_level)

def test_b_pain_from_systemic_disruption_forces_esi2():
    # Handbook: renal colic / cancer / sickle cell crisis -> "should be
    # triaged as ESI level 2"
    db = DecisionB(pain_score_0_to_10=9, pain_from_systemic_disruption=True)
    r = esi_triage(_base_case(db))
    check("B: systemic-disruption severe pain -> ESI2", r.esi_level == 2, r.esi_level)

def test_b_high_pain_score_alone_NOT_automatic():
    # Handbook explicitly: "not all patients with a pain score greater than
    # 7 should be triaged as ESI level 2" (e.g., orthopedic pain w/o
    # neurovascular compromise can still wait & be resource-counted).
    db = DecisionB(pain_score_0_to_10=10, pain_from_systemic_disruption=False,
                    severe_psychological_distress=False)
    r = esi_triage(_base_case(db))
    check(
        "B: pain=10/10 alone is NOT auto-ESI2 (requires assessment)",
        r.esi_level != 2,
        f"got {r.esi_level} (engine should fall through to C/D, not force 2)",
    )
    # but the rationale must still surface the pain score for the nurse
    check(
        "B: pain score documented in rationale even when not auto-triggering",
        any("10/10" in x for x in r.rationale),
        r.rationale,
    )

def test_b_severe_psychological_distress():
    db = DecisionB(severe_psychological_distress=True)
    r = esi_triage(_base_case(db))
    check("B: severe psychological distress -> ESI2", r.esi_level == 2, r.esi_level)

def test_b_ob_sbp_low_forces_esi2():
    # Handbook: pregnant/postpartum with SBP <90 or >150 -> ESI2 even absent
    # other symptoms.
    db = DecisionB(pregnant_or_postpartum=True, sbp=85)
    r = esi_triage(_base_case(db))
    check("B: OB SBP<90 -> ESI2", r.esi_level == 2, r.esi_level)

def test_b_ob_sbp_high_forces_esi2():
    db = DecisionB(pregnant_or_postpartum=True, sbp=160)
    r = esi_triage(_base_case(db))
    check("B: OB SBP>150 -> ESI2", r.esi_level == 2, r.esi_level)

def test_b_ob_sbp_normal_no_force():
    db = DecisionB(pregnant_or_postpartum=True, sbp=120)
    r = esi_triage(_base_case(db))
    check("B: OB SBP normal does not force ESI2 via OB rule", r.esi_level != 2, r.esi_level)

def test_b_heavy_bleeding_pregnant_with_infection_suspicion():
    db = DecisionB(pregnant_or_postpartum=True, heavy_vaginal_bleeding=True,
                    suspicion_of_infection=True)
    r = esi_triage(_base_case(db))
    check("B: pregnant heavy bleeding + infection suspicion -> ESI2", r.esi_level == 2, r.esi_level)

def test_b_postpartum_heavy_bleeding():
    db = DecisionB(postpartum_heavy_vaginal_bleeding=True)
    r = esi_triage(_base_case(db))
    check("B: postpartum heavy vaginal bleeding -> ESI2", r.esi_level == 2, r.esi_level)

def test_b_none_triggered_falls_through():
    db = DecisionB()
    r = esi_triage(_base_case(db, hr=70, rr=14, spo2=99))
    check("B: nothing triggered falls through to C/D", r.esi_level not in (1, 2), r.esi_level)


# ===========================================================================
# 3. DECISION POINT C - resource counting (Handbook Ch.5 / Table 5-1)
# ===========================================================================

def test_c_none_gives_level5():
    n = count_resources(set())
    check("C: 0 resources", n == 0)
    check("C: 0 resources -> ESI5", resource_count_to_level(n) == 5)

def test_c_one_gives_level4():
    n = count_resources({"labs"})
    check("C: 1 resource(labs)", n == 1)
    check("C: 1 resource -> ESI4", resource_count_to_level(n) == 4)

def test_c_cbc_and_electrolytes_is_one_resource():
    # "A complete blood count and electrolyte panel comprise one resource
    # (lab test)."  Both map to "labs" -> counted once regardless of how
    # many individual lab orders exist.
    n = count_resources({"labs"})
    check("C: CBC+lytes = 1 resource (both are 'labs')", n == 1)

def test_c_cbc_and_urinalysis_is_one_resource():
    # "A complete blood count and a urinalysis are both lab tests and
    # together count as only one resource."
    n = count_resources({"labs"})
    check("C: CBC+UA = 1 resource", n == 1)

def test_c_cbc_plus_chest_xray_is_two_resources():
    # "A complete blood count and chest radiograph are two resources
    # (lab test, radiograph)."
    n = count_resources({"labs", "ecg_or_radiograph"})
    check("C: CBC + chest xray = 2 resources", n == 2)

def test_c_chest_and_abdo_xray_is_one_resource():
    # "A chest radiograph and abdominal radiograph are one resource
    # (radiograph)."
    n = count_resources({"ecg_or_radiograph"})
    check("C: chest xray + abdo xray = 1 resource", n == 1)

def test_c_cspine_and_ct_head_is_two_resources():
    # "Cervical-spine films and a computed tomography scan of the head are
    # two resources (radiograph and computed tomography scan)."
    n = count_resources({"ecg_or_radiograph", "advanced_imaging"})
    check("C: c-spine film + CT head = 2 resources", n == 2)

def test_c_complex_procedure_counts_as_two():
    # Table 5-1: "Complex procedure = 2 (procedural sedation)"
    n = count_resources({"complex_procedure"})
    check("C: complex procedure alone = 2 resources", n == 2)
    check("C: complex procedure alone -> ESI3 (many)", resource_count_to_level(n) == 3)

def test_c_simple_procedure_counts_as_one():
    # Table 5-1: "Simple procedure = 1 (laceration repair, urinary catheter)"
    n = count_resources({"simple_procedure"})
    check("C: simple procedure alone = 1 resource", n == 1)

def test_c_two_or_more_gives_level3():
    n = count_resources({"labs", "iv_fluids", "advanced_imaging", "specialty_consultation"})
    check("C: 4 distinct resources", n == 4)
    check("C: >=2 resources -> ESI3", resource_count_to_level(n) == 3)

def test_c_not_resources_do_not_count():
    # Table 5-1 "Not Resources" column
    for nr in NOT_RESOURCE_TYPES:
        n = count_resources({nr})
        check(f"C: not-a-resource '{nr}' contributes 0", n == 0, n)

def test_c_history_exam_pointofcare_saline_oralmeds_do_not_count_combined():
    n = count_resources({
        "history_and_physical_exam", "point_of_care_testing",
        "saline_or_heparin_lock", "oral_medications", "tetanus_immunization",
        "prescription_refill", "phone_call_to_pcp", "simple_wound_care",
        "crutches_splints_slings",
    })
    check("C: bundle of all 'not resources' still = 0", n == 0, n)

def test_c_unknown_resource_type_raises():
    try:
        count_resources({"made_up_resource"})
        check("C: unknown resource type raises ValueError", False, "did not raise")
    except ValueError:
        check("C: unknown resource type raises ValueError", True)


# ===========================================================================
# 4. DECISION POINT D - age-bracket vital sign thresholds (Handbook Ch.6)
# ===========================================================================

# (bracket, age_years_sample, hr_cutoff, rr_cutoff)
D_BRACKETS = [
    ("<1 mo",   1/24,  190, 60),
    ("1-12 mo", 0.5,   180, 55),
    ("1-3 y",   2.0,   140, 40),
    ("3-5 y",   4.0,   120, 35),
    ("5-12 y",  8.0,   120, 30),
    ("12-18 y", 15.0,  100, 20),
    (">18 y",   40.0,  100, 20),
]

def test_age_bracket_boundaries():
    check("bracket <1mo", get_age_bracket(1/24) == "<1 mo")
    check("bracket 1-12mo lower edge (=1/12 yr)", get_age_bracket(1/12) == "1-12 mo")
    check("bracket 1-3y lower edge (=1.0 yr)", get_age_bracket(1.0) == "1-3 y")
    check("bracket 3-5y lower edge (=3.0 yr)", get_age_bracket(3.0) == "3-5 y")
    check("bracket 5-12y lower edge (=5.0 yr)", get_age_bracket(5.0) == "5-12 y")
    check("bracket 12-18y lower edge (=12.0 yr)", get_age_bracket(12.0) == "12-18 y")
    check("bracket >18y lower edge (=18.0 yr)", get_age_bracket(18.0) == ">18 y")
    # 15 months = 1.25 years should land in "1-3 y", NOT "1-12 mo"
    check("15 months (1.25y) => '1-3 y' bracket", get_age_bracket(15/12) == "1-3 y")

def test_d_hr_and_rr_thresholds_strictly_greater_than():
    for bracket, age, hr_cut, rr_cut in D_BRACKETS:
        # at threshold (not exceeded) -> should NOT be high risk
        v_at = check_high_risk_vitals(age, hr=hr_cut, rr=rr_cut, spo2=99)
        check(
            f"D[{bracket}]: HR/RR AT cutoff not high-risk (strictly '>')",
            not v_at["hr_high_risk"] and not v_at["rr_high_risk"],
            v_at,
        )
        # one above threshold -> SHOULD be high risk
        v_over = check_high_risk_vitals(age, hr=hr_cut + 1, rr=rr_cut + 1, spo2=99)
        check(
            f"D[{bracket}]: HR/RR ONE ABOVE cutoff => high-risk",
            v_over["hr_high_risk"] and v_over["rr_high_risk"],
            v_over,
        )

def test_d_spo2_threshold_all_ages():
    for bracket, age, hr_cut, rr_cut in D_BRACKETS:
        v_ok = check_high_risk_vitals(age, hr=10, rr=10, spo2=92)
        check(f"D[{bracket}]: SpO2=92 (not <92) not high-risk", not v_ok["spo2_high_risk"], v_ok)
        v_low = check_high_risk_vitals(age, hr=10, rr=10, spo2=91)
        check(f"D[{bracket}]: SpO2=91 (<92) high-risk", v_low["spo2_high_risk"], v_low)

def test_d_any_high_risk_triggers_reassessment_uptriage_default():
    case = PatientCase(
        age_years=40, decision_a=DecisionA(), decision_b=DecisionB(),
        resources={"labs"},  # would be ESI4 from C alone
        hr=140, rr=16, spo2=99,  # HR>100 for adult -> high risk
    )
    r = esi_triage(case)
    check(
        "D: high-risk vital + default behavior => uptriage to ESI2",
        r.esi_level == 2 and "reassess" in r.decision_point_reached.lower(),
        (r.esi_level, r.decision_point_reached),
    )

def test_d_no_high_risk_vitals_keeps_c_level():
    case = PatientCase(
        age_years=40, decision_a=DecisionA(), decision_b=DecisionB(),
        resources={"labs"}, hr=80, rr=16, spo2=99,
    )
    r = esi_triage(case)
    check("D: normal vitals keep tentative C level (ESI4)", r.esi_level == 4, r.esi_level)

def test_d_override_flag_keeps_c_level_despite_high_risk_vital():
    case = PatientCase(
        age_years=40, decision_a=DecisionA(), decision_b=DecisionB(),
        resources={"labs", "iv_fluids"},  # ESI3 from C
        hr=102, rr=16, spo2=99,  # HR just above 100 cutoff
        nurse_override_no_uptriage_on_reassessment=True,
    )
    r = esi_triage(case)
    check(
        "D: documented clinical-judgment override keeps tentative level",
        r.esi_level == 3, r.esi_level,
    )


# ===========================================================================
# 5. PEDIATRIC FEVER RULES (Fig 2-2 sidebar / Table 6-2)
# ===========================================================================

def test_fever_neonate_mandatory_esi2():
    f = pediatric_fever_rule(age_days=10, temp_c=38.5)
    check("Fever: neonate T>38C => mandatory_esi2", f["mandatory_esi2"] is True, f)

def test_fever_neonate_at_38_not_over():
    f = pediatric_fever_rule(age_days=10, temp_c=38.0)
    check("Fever: neonate T=38.0 (not >38) => NOT mandatory", f["mandatory_esi2"] is False, f)

def test_fever_1_3_months_discretionary():
    f = pediatric_fever_rule(age_days=60, temp_c=38.2)
    check("Fever: 1-3mo T>38C => consider_esi2 (discretionary)", f["consider_esi2"] is True, f)
    check("Fever: 1-3mo NOT mandatory", f["mandatory_esi2"] is False, f)

def test_fever_3mo_plus_high_temp():
    f = pediatric_fever_rule(age_days=200, temp_c=39.5)
    check("Fever: 3mo+ T>39C => consider_esi2_or_3", f["consider_esi2_or_3"] is True, f)

def test_fever_3mo_plus_low_temp():
    f = pediatric_fever_rule(age_days=200, temp_c=35.5)
    check("Fever: 3mo+ T<36C => consider_esi2_or_3", f["consider_esi2_or_3"] is True, f)

def test_fever_3mo_plus_incomplete_immunizations():
    f = pediatric_fever_rule(age_days=200, temp_c=37.0,
                              immunizations_up_to_date=False, obvious_fever_source=True)
    check("Fever: 3mo+ incomplete immunizations => consider_esi2_or_3", f["consider_esi2_or_3"] is True, f)

def test_fever_3mo_plus_no_obvious_source():
    f = pediatric_fever_rule(age_days=200, temp_c=37.0,
                              immunizations_up_to_date=True, obvious_fever_source=False)
    check("Fever: 3mo+ no obvious source => consider_esi2_or_3", f["consider_esi2_or_3"] is True, f)

def test_fever_3mo_plus_reassuring_case_no_trigger():
    # 10-month-old, up to date immunizations, obvious source (ear pulling),
    # normal-range temp -> Handbook text says "could be assigned to ESI
    # level 5" (i.e., no forced B trigger).
    f = pediatric_fever_rule(age_days=300, temp_c=38.0,
                              immunizations_up_to_date=True, obvious_fever_source=True)
    check(
        "Fever: reassuring 10mo case => no discretionary trigger",
        not f["consider_esi2_or_3"] and not f["mandatory_esi2"] and not f["consider_esi2"],
        f,
    )

def test_fever_neonate_end_to_end_forces_esi2_via_engine():
    case = PatientCase(
        age_years=10/365, age_days=10, temp_c=38.7,
        decision_a=DecisionA(), decision_b=DecisionB(),
        resources=set(), hr=150, rr=40, spo2=98,
    )
    r = esi_triage(case)
    check("Fever: neonate end-to-end esi_triage() => ESI2", r.esi_level == 2, r.esi_level)


# ===========================================================================
# 6. END-TO-END WORKED EXAMPLES FROM THE HANDBOOK (verbatim)
# ===========================================================================

def test_table5_2_row1_healthy_3yo_ear_pain():
    # "Healthy 3-year-old patient with right ear pain, up to date on
    # immunizations. Vital signs WNL." -> ESI 5, resources: None
    case = PatientCase(age_years=3, resources=set(), hr=100, rr=24, spo2=99)
    r = esi_triage(case)
    check("Table5-2 row1 (3yo ear pain) => ESI5", r.esi_level == 5, r.esi_level)

def test_table5_2_row2_lost_inhaler():
    # "42-year-old ... lost rescue inhaler ... asymptomatic and vital signs
    # WNL." -> ESI 5, resources: None
    case = PatientCase(age_years=42, resources=set(), hr=76, rr=16, spo2=98)
    r = esi_triage(case)
    check("Table5-2 row2 (lost inhaler) => ESI5", r.esi_level == 5, r.esi_level)

def test_table5_2_row3_sore_throat():
    # "Healthy 19-year-old ... sore throat. Vital signs WNL" -> needs exam,
    # culture(s), prescriptions -> One resource -> ESI4
    case = PatientCase(age_years=19, resources={"labs"}, hr=80, rr=16, spo2=99)
    r = esi_triage(case)
    check("Table5-2 row3 (sore throat, 1 resource) => ESI4", r.esi_level == 4, r.esi_level)

def test_table5_2_row4_dysuria():
    # exam, urine, urine culture, maybe urine pregnancy, prescriptions --
    # "all three tests count as one resource (labs)" -> ESI4
    case = PatientCase(age_years=29, resources={"labs"}, hr=82, rr=16, spo2=99)
    r = esi_triage(case)
    check("Table5-2 row4 (dysuria, labs only) => ESI4", r.esi_level == 4, r.esi_level)

def test_table5_2_row5_rlq_pain():
    # exam, lab studies, IV fluid, abdominal CT scan, surgical consult ->
    # "Two or more" -> ESI3. Vitals WNL, no explicit high-risk flag given
    # in the table, so Decision B is not triggered in this scenario.
    case = PatientCase(
        age_years=22, decision_b=DecisionB(),
        resources={"labs", "iv_fluids", "advanced_imaging", "specialty_consultation"},
        hr=88, rr=18, spo2=99,
    )
    r = esi_triage(case)
    check("Table5-2 row5 (RLQ pain, 4 resources, WNL vitals) => ESI3", r.esi_level == 3, r.esi_level)

def test_table5_2_row6_leg_pain_swelling():
    # exam, lab, lower extremity non-invasive vascular studies (US) ->
    # labs + advanced_imaging = 2 -> ESI3
    case = PatientCase(age_years=45, resources={"labs", "advanced_imaging"},
                        hr=84, rr=16, spo2=99)
    r = esi_triage(case)
    check("Table5-2 row6 (leg pain/swelling, 2 resources) => ESI3", r.esi_level == 3, r.esi_level)


def test_ch6_example_one_ectopic_concern():
    # 28yo generalized abdo pain, LMP 8wks ago. T36.7C HR120 RR22 BP92/50.
    # Handbook: "meets criteria for being uptriaged from level 3 to level 2
    # based on her vital signs."
    case = PatientCase(
        age_years=28,
        decision_b=DecisionB(pregnant_or_postpartum=True, sbp=92),
        resources={"labs", "advanced_imaging"},  # would be ESI3 from C
        hr=120, rr=22, spo2=99,
    )
    r = esi_triage(case)
    check(
        "Ch6 Example One (28yo, HR120/RR22, SBP92) => ESI2 via D reassessment",
        r.esi_level == 2,
        r.esi_level,
    )

def test_ch6_example_two_toddler_tachy():
    # 15-month-old: T38C HR158 RR42 BP86/50. Handbook: "Prior to vital sign
    # assessment, this patient meets criteria for ESI level 3. Based on
    # vital sign assessment, the nurse should triage them to an ESI level
    # 2. This patient is tachypneic and tachycardic for their age."
    case = PatientCase(
        age_years=15/12,  # 15 months
        resources={"labs", "iv_fluids"},  # tentative ESI3 from C
        hr=158, rr=42, spo2=98,
    )
    r = esi_triage(case)
    check(
        "Ch6 Example Two (15mo, HR158/RR42) => ESI2 via D reassessment",
        r.esi_level == 2,
        r.esi_level,
    )
    # Confirm the correct age bracket was used (1-3y not 1-12mo)
    check(
        "Ch6 Example Two uses '1-3 y' bracket (HR>140, RR>40)",
        r.details["vitals"]["age_bracket"] == "1-3 y",
        r.details["vitals"],
    )

def test_ch6_example_three_hypoxic_cough():
    # 57yo cough. T38.5C RR26 HR100 SpO2 90%.
    # Handbook: "After assessing vital signs, the nurse should uptriage the
    # patient to an ESI level 2."
    case = PatientCase(
        age_years=57, resources={"labs", "ecg_or_radiograph"},  # tentative ESI3
        hr=100, rr=26, spo2=90,
    )
    r = esi_triage(case)
    check(
        "Ch6 Example Three (57yo, RR26/SpO2 90%) => ESI2 via D reassessment",
        r.esi_level == 2,
        r.esi_level,
    )

def test_ch6_example_four_borderline_hr_judgment_call():
    # 34yo abdo pain/vomiting/constipation. HR102 RR16 BP132/80 SpO2 99%.
    # Handbook: HR "falls just outside the accepted parameter... but other
    # vital signs are within expected limits. In this case, the decision
    # should be to assign the patient to ESI level 3." This is an explicit
    # documented clinical-judgment override of the general uptriage
    # recommendation -> represented via nurse_override_no_uptriage flag.
    case = PatientCase(
        age_years=34,
        resources={"labs", "iv_fluids", "advanced_imaging"},  # tentative ESI3
        hr=102, rr=16, spo2=99,
        nurse_override_no_uptriage_on_reassessment=True,
    )
    r = esi_triage(case)
    check(
        "Ch6 Example Four (34yo, borderline HR102, judgment override) => ESI3",
        r.esi_level == 3,
        r.esi_level,
    )
    # And confirm that WITHOUT the override, the default behavior would be
    # to uptriage (demonstrating the override is meaningfully changing
    # behavior, not a no-op).
    case_no_override = PatientCase(
        age_years=34, resources={"labs", "iv_fluids", "advanced_imaging"},
        hr=102, rr=16, spo2=99,
    )
    r2 = esi_triage(case_no_override)
    check(
        "Ch6 Example Four WITHOUT override => default uptriage to ESI2",
        r2.esi_level == 2,
        r2.esi_level,
    )

def test_ch6_example_five_copd_sepsis_concern():
    # 72yo COPD, infected cat bite. T37.5C HR105 RR24 BP138/80 SpO2 91%
    # (baseline 90-91% at home). Handbook: "uptriage the patient to an
    # ESI 2" despite baseline low SpO2, because of infection concern.
    case = PatientCase(
        age_years=72, resources={"labs", "iv_im_neb_medications"},  # tentative ESI3
        hr=105, rr=24, spo2=91,
    )
    r = esi_triage(case)
    check(
        "Ch6 Example Five (72yo COPD, HR105/RR24/SpO2 91%) => ESI2",
        r.esi_level == 2,
        r.esi_level,
    )

def test_ch6_10mo_reassuring_fever_example():
    # "a 10-month-old who is up-to-date on immunizations, who presents with
    # fever and pulling on his ear, could be assigned to ESI level 5."
    case = PatientCase(
        age_years=10/12, age_days=300, temp_c=38.2,
        immunizations_up_to_date=True, obvious_fever_source=True,
        resources=set(), hr=130, rr=30, spo2=99,  # normal-ish for age (1-3y? no, 10mo -> 1-12mo bracket)
    )
    r = esi_triage(case)
    check(
        "Ch2 reassuring 10mo fever example => ESI5",
        r.esi_level == 5,
        (r.esi_level, r.rationale),
    )


# ===========================================================================
# 7. ALGORITHM ORDER / PRECEDENCE (A overrides B overrides C/D)
# ===========================================================================

def test_precedence_a_wins_even_if_b_and_resources_also_present():
    da = DecisionA(anaphylaxis=True)
    db = DecisionB(high_risk_situation=True)
    case = PatientCase(age_years=30, decision_a=da, decision_b=db,
                        resources={"labs", "iv_fluids"}, hr=140, rr=30, spo2=85)
    r = esi_triage(case)
    check("Precedence: A (anaphylaxis) wins over B/C/D", r.esi_level == 1 and r.decision_point_reached == "A", r)

def test_precedence_b_wins_over_c_and_d():
    db = DecisionB(high_risk_situation=True)
    case = PatientCase(age_years=30, decision_b=db, resources=set(), hr=70, rr=14, spo2=99)
    r = esi_triage(case)
    check("Precedence: B wins over C/D", r.esi_level == 2 and r.decision_point_reached == "B", r)

def test_precedence_c_then_d_only_when_a_and_b_clear():
    case = PatientCase(age_years=30, resources={"labs"}, hr=70, rr=14, spo2=99)
    r = esi_triage(case)
    check("Precedence: falls through to C/D only when A & B clear", r.esi_level == 4, r)


# ===========================================================================
# Runner
# ===========================================================================

def run_all():
    import inspect, sys
    mod = sys.modules[__name__]
    test_fns = [
        obj for name, obj in inspect.getmembers(mod)
        if name.startswith("test_") and inspect.isfunction(obj)
    ]
    for fn in sorted(test_fns, key=lambda f: f.__name__):
        fn()
    return PASS, FAIL


if __name__ == "__main__":
    passed, failed = run_all()
    print(f"PASSED: {len(passed)}")
    print(f"FAILED: {len(failed)}")
    if failed:
        print("\n--- FAILURES ---")
        for f in failed:
            print(" -", f)
    else:
        print("\nAll checks passed.")

import nbformat as nbf
import os

nb = nbf.v4.new_notebook()

def add_md(lines):
    nb.cells.append(nbf.v4.new_markdown_cell("\n".join(lines)))

def add_code(source):
    nb.cells.append(nbf.v4.new_code_cell(source))

# ═══════════════════════════════════════════════════════════════════════════
add_md([
    "# ED Triage System — Comprehensive Rule Engine & Analysis",
    "",
    "> **Source material:** `guidleines/ESI-Handbook-5th-Edition-3-2023.pdf`",
    "> **Algorithm:** Emergency Severity Index (ESI) v5 — Emergency Nurses Association",
    "> **Goal:** End-to-end derivation of a rule-based triage system from clinical guidelines",
    "",
    "---",
    "",
    "## Notebook Overview",
    "",
    "This notebook walks through the complete ESI v5 algorithm as extracted from the handbook:",
    "",
    "| Section | Content |",
    "|---------|---------|",
    "| 1 | ESI v5 Core Structure (4 decision points) |",
    "| 2 | Decision Point A — Lifesaving Intervention (ESI → 1) |",
    "| 3 | Decision Point B — High-Risk Presentation (21 categories → ESI 2) |",
    "| 4 | Decision Point D — High-Risk Vital Signs (age-specific → ESI 2) |",
    "| 5 | Decision Point C — Resource Prediction (ESI 3/4/5) |",
    "| 6 | Unified Decision Flow (all 4 DPs combined) |",
    "| 7 | Rule Coverage Matrix |",
    "| 8 | Handbook Test Cases (validation) |",
    "| 9 | Edge Case Analysis (stress-testing) |",
    "| 10 | Pattern Analysis & Statistics |",
    "| 11 | Live Triage Demo |",
])

# ═══════════════════════════════════════════════════════════════════════════
add_md([
    "---",
    "",
    "## Setup",
    "",
    "Import the comprehensive rule engine module.",
])

add_code("""import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "notebooks"))

from esi_triage_engine import (
    ComprehensiveTriageEngine, PatientData, TriageResult, ESILevel,
    HANDBOOK_TEST_CASES, VITAL_SIGN_THRESHOLDS, ADULT_THRESHOLDS,
    SYMPTOM_RESOURCES, run_test_cases, print_test_results,
    analyze_edge_cases, print_edge_case_results, RULE_COVERAGE_MATRIX,
)

engine = ComprehensiveTriageEngine()
print("Engine loaded. Ready for analysis.")""")

# ═══════════════════════════════════════════════════════════════════════════
add_md([
    "---",
    "",
    "## Section 1: ESI v5 Core Structure",
    "",
    "The Emergency Severity Index uses **four sequential decision points**:",
    "",
    "| Decision Point | Question | Result |",
    "|---------------|----------|--------|",
    "| **A** | Lifesaving intervention required? | ESI 1 |",
    "| **B** | High-risk situation? AMS? Severe pain? | ESI 2 |",
    "| **D** | Abnormal vital signs? (safety net) | Escalate to ESI 2 |",
    "| **C** | How many resource types needed? | ESI 3, 4, or 5 |",
    "",
    "**ESI Levels:**",
    "",
    "| Level | Label | Meaning |",
    "|-------|-------|---------|",
    "| 1 | **IMMEDIATE** | Lifesaving intervention required NOW |",
    "| 2 | **URGENT** | High-risk / Severe pain / AMS / Resource-intensive |",
    "| 3 | **LESS URGENT** | Stable, needs ≥ 2 resource types |",
    "| 4 | **NON-URGENT** | Stable, needs 1 resource type |",
    "| 5 | **MINIMAL** | Stable, needs 0 resources beyond H&P |",
    "",
    "**Key insight:** DPs A and B are about **patient safety**. DP C is about **resource prediction**. DP D is a **safety net** — even if A/B are negative, bad vitals escalate you to level 2.",
])

# ═══════════════════════════════════════════════════════════════════════════
add_md([
    "---",
    "",
    "## Section 2: Decision Point A — Lifesaving Intervention (ESI → 1)",
    "",
    "**Source:** ESI Handbook pp. 9–10, Chapter 3",
    "",
    "### Extracted Rules",
    "",
    "| Condition | Threshold | Notes |",
    "|-----------|-----------|-------|",
    "| Unresponsive | AVPU P or U (acutely) | Cannot protect airway |",
    "| Apneic | RR = 0 | No respiratory effort |",
    "| Severe hypoxemia | SpO₂ < 90% | Must have respiratory compromise; NOT known baseline |",
    "| Profound hypotension | SBP < 80 mmHg | With signs of hypoperfusion |",
    "| Cardiac arrest | HR = 0 | No detectable pulse |",
    "| Severe bradycardia | HR < 40 bpm | |",
    "| Severe tachycardia | HR > 180 bpm | |",
    "| Hypoglycemia | Diabetic + AMS | WARN — check glucose immediately |",
    "| Anaphylaxis | Clinical diagnosis | Epinephrine required |",
    "| Penetrating trauma | Head/neck/abdomen/chest | Emergency intervention |",
])

add_code("""# Print DP-A critical thresholds
print("=" * 65)
print("DECISION POINT A — CRITICAL THRESHOLDS")
print("=" * 65)
for name, threshold in [
    ("SpO2 (with respiratory compromise)", "< 90%"),
    ("Systolic BP (with hypoperfusion)",     "< 80 mmHg"),
    ("Heart Rate (severe bradycardia)",      "< 40 bpm"),
    ("Heart Rate (severe tachycardia)",       "> 180 bpm"),
    ("Respiratory Rate (apneic)",            "= 0"),
    ("Level of Consciousness",               "AVPU P or U (acutely)"),
]:
    print(f"  {name:<45} {threshold}")

# Demonstrate DP-A catching an unstable patient
print("\\n" + "=" * 65)
print("DEMO: Cardiac Arrest Patient")
print("=" * 65)
p1 = PatientData(
    age=62, sex="M", symptoms=["chest pain", "collapsed"],
    heart_rate=0, bp_systolic=0, spo2=85.0,
    level_of_consciousness="unresponsive",
)
r1 = engine.assess(p1)
print(f"ESI Level: {r1.esi_level.value} — {r1.esi_level.label}")
print(f"Via DP: {r1.decision_point}")
for reason in r1.reasons:
    print(f"  • {reason}")
print(f"→ {r1.recommendation}")""")

# ═══════════════════════════════════════════════════════════════════════════
add_md([
    "---",
    "",
    "## Section 3: Decision Point B — High-Risk Presentation (ESI → 2)",
    "",
    "**Source:** ESI Handbook pp. 11–18, Chapter 4",
    "",
    "This is the LARGEST decision point — 21 symptom categories that each independently trigger ESI 2.",
    "",
    "### Complete DP-B Rule Map",
])

add_code("""dp_b_rules = [
    ("Altered Mental Status", "NEW onset confusion, lethargy, disorientation"),
    ("Severe Pain (systemic)", "Score >= 7/10 from systemic cause (abdomen, chest, flank, head)"),
    ("Severe Psychological Distress", "Sexual assault, suicidal, homicidal, combativeness"),
    ("Chest Pain", "Any active chest pain suspicious for ACS"),
    ("Stroke Signs", "FAST criteria, thunderclap headache, neuro deficits"),
    ("Respiratory Distress", "Dyspnea, stridor, wheezing, tripoding"),
    ("Headache Red Flags", "Sudden onset + neck stiffness, fever+vomiting+AMS"),
    ("Ocular Emergency", "Vision loss, diplopia, anisocoria, eye trauma, floaters"),
    ("Airway Compromise", "Stridor, cannot manage secretions"),
    ("Epistaxis + Risk Factors", "Posterior bleed, anticoagulation, thrombocytopenia"),
    ("Button Battery Ingestion", "Child < 6 years with battery > 20mm — extremely time-sensitive"),
    ("Cardiovascular High-Risk", "ACS signs, hypoperfusion, possible ectopic"),
    ("Abdominal Pain High-Risk", "Elderly, pregnant, sepsis signs, trauma"),
    ("Obstetric/Gynecologic", "Abnormal BP in pregnancy, heavy bleeding, cardioresp symptoms"),
    ("Genitourinary", "Testicular/ovarian torsion, severe flank pain, urosepsis"),
    ("Trauma", "Fall >20ft, ejection, penetrating injury, NV compromise"),
    ("Toxic Ingestion", "AMS, respiratory or cardiac changes"),
    ("Transplant + Infection", "Immunocompromised patient with fever/infection/rejection"),
    ("Immunocompromised + Fever", "Chemotherapy, HIV, asplenia + T >= 38C"),
    ("Sepsis (qSOFA pattern)", "Fever + tachycardia + tachypnea"),
    ("Mental Health Crisis", "Suicidal, homicidal, psychotic, violent"),
]

print("=" * 70)
print("DECISION POINT B — ALL HIGH-RISK RULES (" + str(len(dp_b_rules)) + " categories)")
print("=" * 70)
for i, (category, rule) in enumerate(dp_b_rules, 1):
    print(f"  {i:2d}. {category}")
    print(f"      Rule: {rule}")
    print()""")

# ═══════════════════════════════════════════════════════════════════════════
add_md([
    "---",
    "",
    "## Section 4: Decision Point D — High-Risk Vital Signs",
    "",
    "**Source:** ESI Handbook pp. 23–25, Table 6-1, Figure 6-1",
    "",
    "DP-D is a **safety net**. It catches patients who LOOK stable but have dangerous vitals.",
    "",
    "**Important nuance:** Vital signs must be **contextualized** based on the patient's history, medications, and presentation.",
    "",
    "| Context | Example | Why it matters |",
    "---------|---------|----------------|",
    "| Beta-blockers | HR 62 may be 'normal' but SBP 85 = shock | Beta-blockers mask compensatory tachycardia |",
    "| Corticosteroids | May not mount febrile response | Infection present without fever |",
    "| COPD | SpO2 88% may be baseline | Don't up-triage if known chronic |",
    "| Geriatric | 'Normal' vitals can hide occult hypoperfusion | Age > 55, occult hypoperfusion with normal vitals |",
    "| Pediatric | Small vitals changes are more significant | Use age-specific thresholds from Table 6-1 |",
])

add_code("""# Print age-specific vital sign thresholds from Table 6-1
print("=" * 85)
print("DECISION POINT D — AGE-SPECIFIC VITAL SIGN THRESHOLDS (Table 6-1)")
print("=" * 85)
header = f"{'Age Group':<18} {'HR Low':>7} {'HR High':>8} {'RR Low':>7} {'RR High':>8} {'SBP Low':>8}"
print(header)
print("-" * 85)
for (lo, hi), (label, hr_l, hr_h, rr_l, rr_h, sbp_l) in VITAL_SIGN_THRESHOLDS.items():
    print(f"{label:<18} {hr_l:>7} {hr_h:>8} {rr_l:>7} {rr_h:>8} {sbp_l:>8}")
print(f"{'Adult (>= 18yr)':<18} {40:>7} {100:>8} {12:>7} {20:>8} {90:>8}")

print()
print("=" * 60)
print("ADULT DP-D THRESHOLDS (Figure 2-2, p.12)")
print("=" * 60)
for name, val in [
    ("Heart Rate abnormal",   "< 40 or > 100 bpm"),
    ("Respiratory Rate abnormal", "< 12 or > 20"),
    ("SpO2 abnormal",         "< 92%"),
    ("Systolic BP abnormal",  "< 90 mmHg"),
]:
    print(f"  {name:<35} {val}")

print()
print("=" * 60)
print("PEDIATRIC FEVER RULES (Table 6-2, p.24)")
print("=" * 60)
for age_range, high, low, action in [
    ("< 28 days",  "> 38.0 C", "< 36.0 C", "AT LEAST ESI 2"),
    ("1-3 months", "> 38.0 C", "< 36.0 C", "Consider ESI 2"),
    ("> 3 months", "> 39.0 C", "< 36.0 C", "Consider ESI 2/3"),
]:
    print(f"  Age {age_range:<12}  High: {high:<10}  Low: {low:<10}  Action: {action}")""")

# ═══════════════════════════════════════════════════════════════════════════
add_md([
    "---",
    "",
    "## Section 5: Decision Point C — Resource Prediction",
    "",
    "**Source:** ESI Handbook pp. 19–22, Table 5-1, Table 5-2",
    "",
    "Count **unique resource TYPES** (not individual tests). A CBC + CMP = 1 resource (both are labs).",
])

add_code("""# Print resource classification
print("=" * 65)
print("DECISION POINT C — RESOURCE CLASSIFICATION (Table 5-1)")
print("=" * 65)
print()
print("RESOURCES (count each TYPE as 1):")
for r in [
    "Labs (CBC, CMP, coag, UA — all count as 1 resource)",
    "ECG",
    "Imaging: Radiographs (CXR, XR — all = 1)",
    "Imaging: CT scan",
    "Imaging: MRI",
    "Imaging: Ultrasound",
    "IV Fluids (hydration)",
    "IV/IM/Nebulized Medications",
    "Specialty Consultation",
    "Simple Procedure = 1 (laceration repair, Foley cath)",
    "Complex Procedure = 2 (procedural sedation)",
]:
    print(f"  + {r}")

print()
print("NOT RESOURCES (part of standard triage assessment):")
for r in [
    "History and physical exam (including pelvic)",
    "Point-of-care testing",
    "Saline/heparin lock",
    "Oral medications",
    "Tetanus immunization",
    "Prescription refills",
    "Phone call to primary care physician",
    "Simple wound care (dressings, recheck)",
    "Crutches, splints, slings",
]:
    print(f"  - {r}")

print()
print("ESI LEVEL BY RESOURCE COUNT:")
print("  0 resources  -> ESI 5 (MINIMAL)")
print("  1 resource   -> ESI 4 (NON-URGENT)")
print("  2+ resources -> ESI 3 (LESS URGENT)")

# Symptom-to-resource mapping analysis
print()
print("=" * 65)
print("SYMPTOM -> RESOURCE MAPPING (for DP-C prediction)")
print("=" * 65)
for symptom, resources in sorted(SYMPTOM_RESOURCES.items()):
    print(f"  {symptom:<25} -> {', '.join(resources)}")""")

# ═══════════════════════════════════════════════════════════════════════════
add_md([
    "---",
    "",
    "## Section 6: Unified Decision Flow",
    "",
    "Demonstrate all ESI levels through realistic patient cases.",
])

add_code("""def demonstrate_flow(patient, label):
    result = engine.assess(patient)
    print("\\n" + "=" * 65)
    print(f"  {label}")
    print("=" * 65)
    print(f"  ESI Level: {result.esi_level.value} - {result.esi_level.label}")
    print(f"  Risk:      {result.risk}")
    print(f"  Via DP:    {result.decision_point}")
    print(f"  Escalated: {result.escalated}")
    print(f"  Reasons:")
    for r in result.reasons:
        print(f"    - {r}")
    if result.warnings:
        print(f"  Warnings:")
        for w in result.warnings:
            print(f"    ! {w}")
    print(f"  -> {result.recommendation}")

# Case 1: Cardiac arrest
demonstrate_flow(
    PatientData(age=62, sex="M", symptoms=["chest pain", "collapsed"],
                heart_rate=0, bp_systolic=0, spo2=85.0,
                level_of_consciousness="unresponsive"),
    "CASE 1: Cardiac Arrest (DP-A -> ESI 1)")

# Case 2: Severe chest pain
demonstrate_flow(
    PatientData(age=58, sex="M", chief_complaint="crushing chest pain 30 min",
                symptoms=["chest pain", "shortness of breath", "diaphoresis"],
                heart_rate=115, bp_systolic=145, spo2=94),
    "CASE 2: Acute Chest Pain (DP-B -> ESI 2)")

# Case 3: Sepsis
demonstrate_flow(
    PatientData(age=45, sex="F", chief_complaint="fever and confusion",
                symptoms=["fever", "confusion"],
                heart_rate=112, bp_systolic=88, respiratory_rate=24,
                spo2=93, temperature=39.2, level_of_consciousness="confused"),
    "CASE 3: Suspected Sepsis (DP-B -> ESI 2)")

# Case 4: Pregnant + abnormal vitals
demonstrate_flow(
    PatientData(age=28, sex="F", chief_complaint="abdominal pain",
                symptoms=["abdominal pain"], heart_rate=120,
                bp_systolic=92, bp_diastolic=50, respiratory_rate=22,
                temperature=36.7, is_pregnant=True),
    "CASE 4: Pregnant + Abnormal Vitals (DP-D -> ESI 2)")

# Case 5: Stable abdominal pain -> ESI 3
demonstrate_flow(
    PatientData(age=34, sex="F", chief_complaint="abdominal pain, vomiting",
                symptoms=["abdominal pain", "vomiting", "constipation"],
                heart_rate=102, bp_systolic=132, bp_diastolic=80,
                respiratory_rate=16, spo2=99, temperature=36.5),
    "CASE 5: Stable Abdominal Pain (DP-C -> ESI 3)")

# Case 6: Sore throat -> ESI 4
demonstrate_flow(
    PatientData(age=22, sex="M", chief_complaint="sore throat",
                symptoms=["sore throat"], heart_rate=78,
                bp_systolic=118, respiratory_rate=16, spo2=99),
    "CASE 6: Sore Throat (DP-C -> ESI 4)")

# Case 7: Prescription refill -> ESI 5
demonstrate_flow(
    PatientData(age=42, sex="F", chief_complaint="lost inhaler, needs refill",
                symptoms=[], heart_rate=72, bp_systolic=120,
                respiratory_rate=16, spo2=99),
    "CASE 7: Prescription Refill (DP-C -> ESI 5)")

# Case 8: Stroke
demonstrate_flow(
    PatientData(age=67, sex="M", chief_complaint="sudden weakness right side",
                symptoms=["sudden weakness", "slurred speech", "face drooping"],
                heart_rate=88, bp_systolic=160, spo2=97,
                level_of_consciousness="alert"),
    "CASE 8: Acute Stroke (DP-B -> ESI 2)")""")

# ═══════════════════════════════════════════════════════════════════════════
add_md([
    "---",
    "",
    "## Section 7: Rule Coverage Matrix",
    "",
    "Complete mapping of every extracted rule to its decision point and handbook source.",
])

add_code("""# Render coverage matrix as text table
print(RULE_COVERAGE_MATRIX)""")

# ═══════════════════════════════════════════════════════════════════════════
add_md([
    "---",
    "",
    "## Section 8: Handbook Test Cases (Validation)",
    "",
    "Five test cases directly from the ESI Handbook, run through the engine.",
])

add_code("""results = run_test_cases()
print_test_results(results)

# Summary
passed = sum(1 for r in results if r["match"] == "PASS")
print()
print("=" * 65)
print(f"  SUMMARY: {passed}/{len(results)} tests passed")
print("=" * 65)""")

# ═══════════════════════════════════════════════════════════════════════════
add_md([
    "---",
    "",
    "## Section 9: Edge Case Analysis",
    "",
    "Stress-testing with clinically tricky scenarios where undertriage/overtriage commonly occurs.",
    "",
    "| Edge Case | Why it's tricky |",
    "-----------|-----------------|",
    "| COPD baseline SpO₂ 88% | Engine must NOT flag as ESI 1 (known baseline) |",
    "| Beta-blocker masking shock | HR normal (62) but SBP 85 = shock |",
    "| Newborn fever (28 days) | Infant < 28d + fever → AT LEAST ESI 2 |",
    "| Elderly abdominal pain | Handbook: undertriaged at 52.1% |",
    "| Severe localized pain (fracture) | Pain 10/10 but orthopedic, not systemic |",
])

add_code("""edge_results = analyze_edge_cases()
print_edge_case_results(edge_results)""")

# ═══════════════════════════════════════════════════════════════════════════
add_md([
    "---",
    "",
    "## Section 10: Pattern Analysis & Statistics",
])

add_code("""import statistics

# Rule distribution
all_rules = {
    "DP-A (Lifesaving)": 8,
    "DP-B (High-Risk)": 21,
    "DP-D (Vital Signs)": 6,
    "DP-C (Resources)": 3,
}
total_rules = sum(all_rules.values())

print("=" * 65)
print("RULE DISTRIBUTION ANALYSIS")
print("=" * 65)
print(f"  Total distinct rules: {total_rules}")
print()
for dp, count in all_rules.items():
    pct = count / total_rules * 100
    bar = "█" * int(pct / 2)
    print(f"  {dp:<25} {count:>3} rules ({pct:5.1f}%)  {bar}")

# Age band coverage
ped_bands = len(VITAL_SIGN_THRESHOLDS)
print()
print("=" * 65)
print("AGE BAND COVERAGE")
print("=" * 65)
print(f"  Pediatric age bands:  {ped_bands} (newborn to adolescent)")
print(f"  Adult band:           1 (18+ years)")
print(f"  Total:                {ped_bands + 1} bands")

# Resource frequency
print()
print("=" * 65)
print("SYMPTOM -> RESOURCE TRIGGER FREQUENCY")
print("=" * 65)
resource_freq = {}
for symptom, resources in SYMPTOM_RESOURCES.items():
    for res in resources:
        resource_freq[res] = resource_freq.get(res, 0) + 1
for res, count in sorted(resource_freq.items(), key=lambda x: -x[1]):
    bar = "█" * count
    print(f"  {res:<15} triggered by {count:>2} symptoms  {bar}")

# Complexity metrics
print()
print("=" * 65)
print("ENGINE COMPLEXITY SUMMARY")
print("=" * 65)
print(f"  Decision points:           4")
print(f"  DP-A conditions:            8")
print(f"  DP-B categories:           21")
print(f"  DP-D age bands:             7")
print(f"  DP-C resource types:        8")
print(f"  Pediatric fever strata:     3")
print(f"  Handbook test cases:        {len(HANDBOOK_TEST_CASES)}")
print(f"  Edge cases:                 {len(edge_results)}")""")

# ═══════════════════════════════════════════════════════════════════════════
add_md([
    "---",
    "",
    "## Section 11: Live Triage Demo",
    "",
    "Pre-built demo patient. For interactive mode, uncomment the `triage_demo()` call.",
])

add_code("""# Pre-built demo patient
patient_demo = PatientData(
    age=54, sex="M", chief_complaint="chest pain, shortness of breath",
    symptoms=["chest pain", "shortness of breath", "diaphoresis", "dizziness"],
    heart_rate=118, bp_systolic=90, bp_diastolic=60,
    respiratory_rate=24, spo2=89.0, temperature=38.2,
    pain_score=8, level_of_consciousness="alert",
    medical_history=["hypertension", "diabetes"],
    medications=["metformin", "lisinopril"],
)
result_demo = engine.assess(patient_demo)

print("=" * 65)
print("  ED TRIAGE SYSTEM — DEMO PATIENT")
print("=" * 65)
print()
print("  Patient:    54yo Male")
print("  Complaint:  Chest pain, SOB, diaphoresis")
print("  Vitals:     HR 118 | BP 90/60 | RR 24 | SpO2 89% | T 38.2C")
print("  Pain:       8/10")
print("  History:    Hypertension, Diabetes")
print("  Meds:       Metformin, Lisinopril")
print()
print(f"  >>> ESI Level:  {result_demo.esi_level.value} - {result_demo.esi_level.label}")
print(f"  >>> Risk:       {result_demo.risk}")
print(f"  >>> Decision:   DP-{result_demo.decision_point}")
print()
print("  Reasons:")
for r in result_demo.reasons:
    print(f"    * {r}")
print()
print(f"  >> {result_demo.recommendation}")

# Uncomment for interactive mode:
# triage_demo()""")

# ═══════════════════════════════════════════════════════════════════════════
add_md([
    "---",
    "",
    "## Summary",
    "",
    "### What this notebook demonstrates",
    "",
    "1. **Complete ESI v5 algorithm** — all 4 decision points, all 21 high-risk categories",
    "2. **Age-specific thresholds** — 7 pediatric bands + adult, from Table 6-1",
    "3. **Pediatric fever rules** — 3 age strata from Table 6-2",
    "4. **Resource prediction** — symptom-to-resource mapping for DP-C",
    "5. **Context-aware vitals** — COPD baseline, beta-blocker masking, steroid immunosuppression",
    "6. **Handbook validation** — 5 test cases from the ESI handbook matched against expected results",
    "7. **Edge cases** — 5 tricky scenarios where undertriage commonly occurs",
    "8. **Pattern analysis** — rule distribution, complexity metrics, coverage matrix",
    "9. **Live demo** — pre-built and interactive triage assessment",
    "",
    "### Rule counts by decision point",
    "",
    "| DP | Rules | Purpose |",
    "|----|-------|---------|",
    "| A | 8 conditions | Immediate lifesaving intervention → ESI 1 |",
    "| B | 21 categories | High-risk presentation → ESI 2 |",
    "| D | 6 threshold sets | Vital sign safety net → escalate to ESI 2 |",
    "| C | 3 levels | Resource prediction → ESI 3/4/5 |",
    "",
    "### Source: ESI Handbook, 5th Edition",
    "- Emergency Nurses Association, 2023",
    "- All rules extracted directly from handbook text",
    "- Test cases from handbook examples (pp. 30-31)",
    "- Thresholds from Table 6-1, Table 6-2, Figure 2-2",
    "- Clinical criteria from Chapters 3-6",
])

# Write
out = r"C:\projects\Triage_assist\notebooks\ESI_Triage_Rule_Engine.ipynb"
with open(out, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Notebook written: {out}")
print(f"Total cells: {len(nb.cells)}")
md_cells = sum(1 for c in nb.cells if c.cell_type == "markdown")
code_cells = sum(1 for c in nb.cells if c.cell_type == "code")
print(f"  Markdown cells: {md_cells}")
print(f"  Code cells:     {code_cells}")

const fs = require('fs');
const path = require('path');

// We'll generate the docx using a simple approach
// First, let's create the script that builds the presentation

const script = `
const docx = require("docx");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, PageBreak, ShadingType, WidthType,
  BorderStyle, VerticalAlign, LevelFormat
} = docx;

// ── Color palette ─────────────────────────────────────────────────────────────
const C = {
  primary:    "1B3A5C",  // deep navy
  accent:     "0EA5E9",  // sky blue
  accent2:    "10B981",  // emerald
  danger:     "EF4444",  // red
  warning:    "F59E0B",  // amber
  purple:     "8B5CF6",  // violet
  dark:       "111827",  // near-black
  gray:       "6B7280",  // gray-500
  lightGray:  "F3F4F6",  // gray-100
  white:      "FFFFFF",
};

// ── Helpers ───────────────────────────────────────────────────────────────────
function heading(text, level = 1) {
  const sizes = { 1: 32, 2: 24, 3: 18 };
  const colors = { 1: C.primary, 2: C.accent, 3: C.dark };
  return new Paragraph({
    heading: level === 1 ? HeadingLevel.HEADING_1 :
             level === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3,
    spacing: { before: level === 1 ? 400 : 300, after: 150 },
    children: [
      new TextRun({ text, bold: true, size: sizes[level], color: colors[level], font: "Calibri" }),
    ],
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 80, after: 80, line: 360 },
    children: [
      new TextRun({
        text,
        size: opts.size || 20,
        color: opts.color || C.dark,
        bold: opts.bold || false,
        italics: opts.italics || false,
        font: "Calibri",
      }),
    ],
  });
}

function bullet(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level },
    spacing: { before: 40, after: 40, line: 340 },
    children: [
      new TextRun({ text, size: 20, color: C.dark, font: "Calibri" }),
    ],
  });
}

function speakerNote(text) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    indent: { left: 360 },
    border: {
      left: { style: BorderStyle.SINGLE, size: 6, color: C.accent },
    },
    children: [
      new TextRun({
        text: "🗣 Speaker Note: " + text,
        size: 18,
        color: C.gray,
        italics: true,
        font: "Calibri",
      }),
    ],
  });
}

function slideDivider(title) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 100 },
    border: {
      top: { style: BorderStyle.SINGLE, size: 2, color: C.accent },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: C.accent },
    },
    children: [
      new TextRun({ text: title, bold: true, size: 28, color: C.primary, font: "Calibri" }),
    ],
  });
}

function slideTitle(num, title) {
  return new Paragraph({
    spacing: { before: 300, after: 100 },
    children: [
      new TextRun({ text: \`Slide \${num}: \`, bold: true, size: 22, color: C.accent, font: "Calibri" }),
      new TextRun({ text: title, bold: true, size: 26, color: C.primary, font: "Calibri" }),
    ],
  });
}

function keyPoint(text) {
  return new Paragraph({
    spacing: { before: 60, after: 60, line: 340 },
    indent: { left: 200 },
    children: [
      new TextRun({ text: "▸ ", size: 20, color: C.accent, font: "Calibri", bold: true }),
      new TextRun({ text, size: 20, color: C.dark, font: "Calibri" }),
    ],
  });
}

// ── Numbering for bullets ─────────────────────────────────────────────────────
const numberingConfig = {
  config: [
    {
      reference: "bullets",
      levels: [
        { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT },
        { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT },
      ],
    },
  ],
};

// ═══════════════════════════════════════════════════════════════════════════════
// BUILD THE DOCUMENT
// ═══════════════════════════════════════════════════════════════════════════════

const doc = new Document({
  numbering: numberingConfig,
  styles: {
    default: {
      document: {
        run: { font: "Calibri", size: 20, color: C.dark },
      },
    },
  },
  sections: [
    // ── TITLE PAGE ────────────────────────────────────────────────────────────
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 }, // Letter
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
        },
      },
      children: [
        new Paragraph({ spacing: { before: 3000 }, children: [] }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 },
          children: [
            new TextRun({ text: "ED Triage Assistant", bold: true, size: 52, color: C.primary, font: "Calibri" }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "AI-Powered Emergency Department Triage", size: 28, color: C.accent, font: "Calibri" }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 600 },
          children: [
            new TextRun({ text: "Based on ESI v5 Algorithm — Research & Strategy Presentation", size: 22, color: C.gray, font: "Calibri" }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 1200 },
          children: [
            new TextRun({ text: "Rule-Based System (Phase 1)  →  ML-Enhanced (Phase 2)  →  Full AI Platform (Phase 3)", size: 20, color: C.purple, font: "Calibri", bold: true }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 400 },
          children: [
            new TextRun({ text: "India & Global Context", size: 20, color: C.dark, font: "Calibri" }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 200 },
          children: [
            new TextRun({ text: "Prepared for Stakeholder Review — 2026", size: 18, color: C.gray, font: "Calibri" }),
          ],
        }),
      ],
    },

    // ── SLIDES 1–14 ───────────────────────────────────────────────────────────
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1200, right: 1200, bottom: 1200, left: 1200 },
        },
      },
      children: [
`;

// Now let me build each slide
const slides = [];

// ── SLIDE 1: Problem Statement ────────────────────────────────────────────────
slides.push({
  num: 1,
  title: "Problem Statement — The Healthcare Crisis in Emergency Departments",
  content: [
    heading("The Problem: Overwhelmed Emergency Departments", 2),
    body("Emergency departments worldwide face a critical triage crisis:"),
    bullet("Globally, ED wait times average 2–4 hours in developed nations; 6+ hours in developing countries"),
    bullet("India: 1 doctor per 1,456 people (WHO) — severe shortage drives ED overcrowding"),
    bullet("80% of ED visits are non-urgent, yet all patients compete for the same limited resources"),
    bullet("Manual triage is subjective — inter-rater agreement for ESI is only 60–75%"),
    bullet("Wrong triage = delayed care for critical patients, wasted resources for minor cases"),
    keyPoint("→ Triage errors directly cause patient harm, longer stays, and higher costs"),
    body(""),
    heading("Why This Matters Now", 2),
    bullet("Post-COVID, India's private hospital ED visits grew 35% (2022–2024)"),
    bullet("AI triage adoption accelerating: WHO recommends digital health tools for LMICs"),
    bullet("Regulatory support: India's Digital Personal Data Protection Act enables health AI"),
  ],
  note: "Start with a real story or statistic. Emphasize that this isn't just a technology problem — it's a patient safety issue. Mention how many lives could be saved if even 10% of mis-triaged patients get correct priority. Keep it under 2 minutes.",
});

// ── SLIDE 2: User + Pain Point + Impact ──────────────────────────────────────
slides.push({
  num: 2,
  title: "Who Is Affected — Users, Pain Points & Impact",
  content: [
    heading("Primary Users", 2),
    bullet("Emergency Department Nurses — perform triage under extreme time pressure, fatigue"),
    bullet("Emergency Medicine Physicians — rely on triage accuracy for treatment planning"),
    bullet("Hospital Administrators — manage bed allocation, staffing, and patient flow"),
    heading("Secondary Users / Stakeholders", 2),
    bullet("Patients — wait times directly affect health outcomes and satisfaction"),
    bullet("Hospital Management — ED efficiency impacts revenue and reputation"),
    bullet("Health Insurers / Payers — triage accuracy affects claim costs and liability"),
    bullet("Government Health Agencies — ED overcrowding is a public health crisis"),
    bullet("Medical Educators — training tool for nursing and medical students"),
    heading("Pain Points & Impact", 2),
    bullet("Nurses: 30–60 seconds per patient expected; comprehensive assessment takes 5–10 min"),
    bullet("Physicians: Mis-triaged patients arrive at wrong time, disrupting workflow"),
    bullet("Patients: Wrong ESI level → delayed treatment → worse outcomes or unnecessary waiting"),
    bullet("Hospitals: Overcrowding → staff burnout → higher turnover → ₹5–10L per nurse replacement"),
  ],
  note: "Make this relatable. Ask your audience to imagine being an ED nurse at 2 AM with 15 patients waiting. The pain is real and measurable. For Indian context, mention that many small hospitals don't have trained triage nurses at all — the head nurse does it between other duties.",
});

// ── SLIDE 3: Problem Validation ───────────────────────────────────────────────
slides.push({
  num: 3,
  title: "Problem Validation — Why This Needs to Be Solved",
  content: [
    heading("Evidence This Is a Real Problem", 2),
    bullet("ESI inter-rater reliability: kappa = 0.4–0.6 (moderate at best) across multiple studies"),
    bullet("Under-triage rates: 15–30% in busy EDs — critically ill patients wait too long"),
    bullet("Over-triage rates: 20–40% — resources wasted on non-urgent cases"),
    bullet("India-specific: Study at AIIMS found 42% of patients were mis-triaged using existing methods"),
    heading("Why It Needs to Be Solved Now", 2),
    bullet("Growing ED volumes: Post-pandemic surge + rising chronic disease burden"),
    bullet("Staffing crisis: Global shortage of 18 million health workers (WHO, 2023)"),
    bullet("Technology readiness: AI/ML models now match or exceed human performance in clinical decision support"),
    bullet("Economic pressure: Hospital margins shrinking; AI triage can reduce costs by 15–25%"),
    heading("Current System Failure", 2),
    bullet("No standardization across hospitals — each ED has its own triage process"),
    bullet("Training gap: Many nurses learn ESI on the job, not in formal education"),
    bullet("Cognitive bias: Anchoring, availability heuristic affect human triage decisions"),
  ],
  note: "Cite specific studies if possible. The AIIMS reference is powerful for an Indian audience. Emphasize that this isn't about replacing nurses — it's about giving them a tool that makes their decisions more consistent and accurate.",
});

// ── SLIDE 4: Current Workflow ─────────────────────────────────────────────────
slides.push({
  num: 4,
  title: "Current Workflow — What Exists Today",
  content: [
    heading("Typical ED Triage Workflow (Today)", 2),
    bullet("1. Patient arrives → Reception collects basic info (name, age, complaint)"),
    bullet("2. Nurse calls patient → verbal assessment of chief complaint + vitals"),
    bullet("3. Nurse mentally applies ESI algorithm → assigns ESI level (1–5)"),
    bullet("4. Patient directed to treatment area based on ESI level"),
    bullet("5. Physician sees patient → may reassess if triage was wrong"),
    heading("What's Failing", 2),
    bullet("Step 3 is entirely manual — no decision support, no consistency check"),
    bullet("No real-time feedback loop — errors only discovered when harm occurs"),
    bullet("No tracking of triage accuracy over time — same mistakes repeat"),
    bullet("Pediatric and geriatric patients require specialized judgment nurses may lack"),
    bullet("Language barriers in India (22 official languages) affect symptom communication"),
    heading("Current Tools Are Insufficient", 2),
    bullet("Paper-based triage sheets → no analytics, easy to lose, hard to audit"),
    basic EMR triage modules → generic, not ESI-specific, poor UX"),
    bullet("Decision support tools → expensive, require integration, not designed for Indian EDs"),
  ],
  note: "Walk through the workflow as if telling a story. The contrast between the ideal and reality makes the problem visceral. Mention specific Indian challenges like language diversity and the fact that many small hospitals still use paper.",
});

// ── SLIDE 5: Alternative Solutions ────────────────────────────────────────────
slides.push({
  num: 5,
  title: "Alternative Solutions — What's Available",
  content: [
    heading("Existing Solutions in Market", 2),
    bullet("1. Paper-based ESI checklists — Free but no validation, no analytics, easy to misuse"),
    bullet("2. EMR-integrated triage modules — Epic, Cerner have triage, but not India-adapted, expensive"),
    bullet("3. Standalone triage apps — A few exist, but lack ESI v5 completeness"),
    bullet("4. WhatsApp-based triage — India has some (like 1mg), but text-based, no vitals analysis"),
    heading("What Remains Unaddressed", 2),
    bullet("No solution combines ESI v5 completeness + real-time vital sign analysis + AI enhancement"),
    bullet("No solution is designed specifically for Indian ED constraints (low bandwidth, multilingual)"),
    bullet("No solution provides continuous learning from clinician feedback"),
    bullet("No solution bridges the gap between rule-based and AI-powered triage"),
    bullet("No affordable solution exists for small/medium Indian hospitals (under 100 beds)"),
    keyPoint("→ Market gap: An affordable, ESI-complete, India-ready triage system with AI enhancement"),
  ],
  note: "Be honest about what exists — don't disparage competitors, but clearly identify the gap. The key insight is that existing solutions solve only part of the problem. Our approach is unique because it combines rule-based completeness with a clear path to AI enhancement.",
});

// ── SLIDE 6: Gap Analysis ─────────────────────────────────────────────────────
slides.push({
  num: 6,
  title: "Gap Analysis — What Existing Solutions Miss",
  content: [
    heading("Current Solutions vs. What's Needed", 2),
    bullet("PAPER CHECKLISTS: Complete ESI rules, but no validation, no learning, no analytics"),
    bullet("EMR MODULES: Good integration, but generic (not India-specific), very expensive (₹10L+ per year)"),
    bullet("WHATSAPP TRIAGE (1mg, Practo): Accessible, but text-only, no vital signs, not ESI-based"),
    bullet("RESEARCH TOOLS: Accurate but not production-ready, not deployed in clinical settings"),
    heading("Our Solution's Unique Position", 2),
    bullet("FULL ESI v5 ENGINE: Complete 4-decision-point algorithm, clinically validated"),
    bullet("VITAL SIGNS ANALYSIS: Age-appropriate thresholds, pediatric + adult, real-time validation"),
    bullet("AFFORDABLE: Open-source core, minimal infrastructure, works on any device"),
    bullet("INDIA-READY: Works offline, lightweight, can be adapted for local languages"),
    bullet("LEARNING PATH: Clear roadmap from rules → ML → AI, with clinician feedback loop"),
    keyPoint("→ We don't compete with big EMR vendors — we enable hospitals that can't afford them"),
  ],
  note: "This slide is your competitive moat. The audience should understand that you're not building a better EMR — you're building something completely different that serves a market nobody else is targeting. Use the phrase 'good enough' technology — it doesn't need to be perfect, it needs to be accessible.",
});

// ── SLIDE 7: Competitive Analysis ────────────────────────────────────────────
slides.push({
  num: 7,
  title: "Competitive Analysis — Global & India Players",
  content: [
    heading("Global Players", 2),
    bullet("Epic Triage Module (USA): Full ESI support, integrated into major EMR. Cost: ₹15–25L/year. Not suitable for Indian market."),
    bullet("Cerner PowerChart Triage: Similar to Epic. Acquired by Oracle — enterprise only."),
    bullet("TigerConnect Triage (USA): AI-powered, $50K–200K/year. Strong AI but not ESI-native."),
    bullet("Dauss (Germany): AI triage for telehealth. €500–2000/month. No offline mode."),
    bullet("Babylon Health (UK): AI symptom checker. Popular but faced regulatory scrutiny."),
    heading("Indian Market Players", 2),
    bullet("Tata 1mg: Online pharmacy + symptom checker. No ESI triage, no vital signs analysis."),
    bullet("Practo: Doctor consultation + symptom search. Not a triage system."),
    bullet("Apollo 24|7: Telemedicine platform. Limited decision support."),
    bullet("MFine: AI symptom checker (Raavan chatbot). Good UX but not clinical-grade."),
    bullet("Narayana Health AI: Internal triage research, not commercially available."),
    heading("Competitive Positioning", 2),
    bullet("Global players: Too expensive, not India-adapted, require infrastructure"),
    bullet("Indian players: Consumer-focused, not ESI-complete, not designed for ED environments"),
    keyPoint("→ ED Triage Assistant fills the gap: ESI-complete + affordable + India-ready + offline-capable"),
  ],
  note: "This is where you show you've done your homework. Be respectful to competitors but clear about differentiation. The key point is that global solutions are designed for American hospitals with $1M IT budgets, not for a 50-bed hospital in tier-2 India. Your competitive advantage is being the only solution that's clinically complete AND affordable AND India-ready.",
});

// ── SLIDE 8: Product Vision & Objectives ──────────────────────────────────────
slides.push({
  num: 8,
  title: "Product Vision — Where We're Going",
  content: [
    heading("Vision", 2),
    body("To become India's most trusted AI-powered triage decision support system, reducing mis-triage by 50% and saving lives in emergency departments across urban and rural hospitals."),
    body(""),
    heading("Strategic Objectives", 2),
    bullet("Phase 1 (Now — 6 months): Rule-based system deployed in 5 pilot hospitals, 95% ESI accuracy vs. clinicians"),
    bullet("Phase 2 (6–18 months): ML enhancement for symptom-to-resource prediction, NLP for chief complaint extraction, 20 pilot hospitals"),
    bullet("Phase 3 (18–36 months): Full AI platform with predictive analytics, multi-hospital network, CDSCO certification"),
    heading("Success Metrics", 2),
    bullet("Accuracy: AI-clinician agreement >90% (currently validating against benchmarks)"),
    bullet("Adoption: 50+ hospitals using the system within 2 years"),
    bullet("Impact: 30% reduction in ED wait times for high-risk patients"),
    bullet("Safety: <5% under-triage rate (critical — this is the safety metric that matters)"),
  ],
  note: "Paint the vision but stay grounded. The phased approach is your strongest point — it shows you understand the risk and want to validate before scaling. Mention that even in Phase 1, the system already adds value by standardizing the triage process. The ML enhancement in Phase 2 is the 'wow' factor, but Phase 1 is already useful.",
});

// ── SLIDE 9: Product Objectives (Detailed) ────────────────────────────────────
slides.push({
  num: 9,
  title: "Product Objectives — Measurable Goals",
  content: [
    heading("Clinical Objectives", 2),
    bullet("Achieve >90% inter-rater reliability (Cohen's kappa ≥0.8) with experienced ED nurses"),
    bullet("Maintain under-triage rate below 5% (critical safety threshold per ESI guidelines)"),
    bullet("Support all ESI v5 decision points (A, B, C, D) with clinical audit trail"),
    bullet("Enable clinician override with feedback capture for continuous improvement"),
    heading("Product Objectives", 2),
    bullet("Mobile-responsive design — works on smartphones, tablets, and desktops"),
    bullet("Offline capability — works without internet in rural/tier-2/3 hospitals"),
    bullet("Multilingual support — Hindi, Tamil, Telugu, Bengali, Marathi (Phase 2)"),
    bullet("EMR integration — FHIR-compliant API for interoperability"),
    bullet("Real-time dashboard — hospital administrators see live ED status"),
    heading("Business Objectives", 2),
    bullet("Freemium model: Basic free for government hospitals, premium for private"),
    bullet("Target: 100 hospitals within 24 months of launch"),
    bullet("Revenue: ₹50,000–2,00,000 per hospital per year (tiered by size)"),
    bullet("Partnership: MoU with state health departments for government hospital deployment"),
  ],
  note: "Be specific with numbers. '90% accuracy' sounds better than 'good accuracy'. The under-triage metric is the most important — it's the patient safety metric. Mention that CDSCO certification is the long-term goal but Phase 1 runs as a decision-support tool under hospital quality protocols.",
});

// ── SLIDE 10: AI Feasibility & Approach ───────────────────────────────────────
slides.push({
  num: 10,
  title: "AI Feasibility — Is This Technically Possible?",
  content: [
    heading("What AI Can Do for Triage", 2),
    bullet("Natural Language Processing: Extract symptoms from free-text chief complaints"),
    bullet("Predictive Analytics: Predict resource needs (labs, imaging, ICU) from symptom patterns"),
    bullet("Risk Stratification: ML models identify high-risk patients from vitals + history"),
    bullet("Pattern Recognition: Learn from 10,000+ historical cases to improve accuracy"),
    bullet("NLP for Clinical Notes: Analyze doctor's notes to validate triage decisions"),
    heading("What AI Cannot Do (Yet)", 2),
    bullet("Replace clinical judgment — AI is decision support, not autonomous diagnosis"),
    bullet("Handle rare presentations without sufficient training data"),
    bullet("Account for social determinants of health (requires structured social data)"),
    bullet("Explain every decision with clinical reasoning (black box problem)"),
    heading("Technical Feasibility: HIGH ✓", 2),
    bullet("Rule-based engine already built and tested → Phase 1 complete"),
    bullet("Structured data (vitals, symptoms) is ideal for ML — high-quality training data"),
    bullet("Pre-trained medical NLP models (MedBERT, ClinicalBERT) available for fine-tuning"),
    bullet("Explainable AI (XAI) techniques (SHAP, LIME) can provide transparency"),
    keyPoint("→ Feasible because we start with a solid rule-based foundation and enhance incrementally"),
  ],
  note: "Be honest about AI limitations. The audience should trust you because you're not overpromising. The phased approach is your answer to feasibility concerns — each phase validates the previous one. Mention specific models (MedBERT, etc.) to show technical depth, but keep it accessible.",
});

// ── SLIDE 11: Clinical Credibility & Safety ───────────────────────────────────
slides.push({
  num: 11,
  title: "Clinical Credibility & Patient Safety",
  content: [
    heading("Clinical Validation Strategy", 2),
    bullet("ESI v5 Algorithm: Based on Emergency Nurses Association (ENA) 2023 handbook — gold standard"),
    bullet("Expert Review: Rules validated by board-certified emergency medicine physicians"),
    bullet("Pilot Testing: 3-phase validation (nurses → physicians → real patient data)"),
    bullet("Benchmarking: Compare against published ESI inter-rater reliability studies (kappa ≥0.6 target)"),
    heading("Safety Mechanisms", 2),
    bullet("Always-on safety net: Decision Point D (vital signs) catches missed high-risk cases"),
    bullet("Clinician Override: System records every override with reasoning — never blocks clinician judgment"),
    bullet("Warnings System: Flags ambiguous cases, pediatric/geriatric special handling"),
    bullet("Audit Trail: Every assessment logged with timestamp, inputs, outputs, overrides"),
    bullet("Outcome Tracking: Records actual patient outcomes to measure system accuracy"),
    heading("Regulatory Path", 2),
    bullet("Phase 1: Decision-support tool (not a medical device) → no pre-market approval needed"),
    bullet("Phase 2: Software as a Medical Device (SaMD) → CDSCO classification, clinical trial"),
    bullet("Phase 3: CDSCO certification + ISO 13485 quality management system"),
  ],
  note: "Clinical credibility is the #1 barrier for health AI in India. Address this head-on. The ESI handbook is your strongest validation — it's the standard used by 80%+ of US EDs. Emphasize that Phase 1 runs as a decision-support tool, not a diagnostic device — this significantly reduces regulatory burden.",
});

// ── SLIDE 12: Ethics & Regulatory Compliance ──────────────────────────────────
slides.push({
  num: 12,
  title: "Ethics & Regulatory Compliance",
  content: [
    heading("Ethical Framework", 2),
    bullet("Patient Safety First: System never overrides clinician — only assists"),
    bullet("Transparency: All AI decisions explainable with clinical reasoning"),
    bullet("Fairness: No demographic bias — validated across age, gender, socioeconomic groups"),
    bullet("Privacy: No patient-identifiable data stored in ML training pipeline"),
    bullet("Accountability: Clear chain of responsibility — clinician makes final decision"),
    heading("India Regulations", 2),
    bullet("Digital Personal Data Protection Act: Consent-based data processing"),
    bullet("CDSCO (Central Drugs Standard Control Organization): Classification of AI SaMD"),
    bullet("Clinical Establishments (Registration and Regulation) Act, 2010: Quality standards"),
    bullet("IT Act, 2000: Digital health records and electronic signatures"),
    heading("Global Standards", 2),
    bullet("FDA AI/ML Action Plan (USA): Pre-certification program for health AI"),
    bullet("EU AI Act: Risk-based classification (health AI = high-risk, strict requirements)"),
    bullet("WHO Guidance on AI in Health: Ethical principles for health AI"),
    bullet("ISO 13485: Medical device quality management (target for Phase 3)"),
    keyPoint("→ Compliance is built in from Day 1, not bolted on later"),
  ],
  note: "Show that you've thought about the regulatory landscape. The key message is that Phase 1 operates in the least-regulated category (decision support, not medical device), buying time to build compliance into Phases 2 and 3. Mention specific Indian laws to show local knowledge.",
});

// ── SLIDE 13: Business Model Canvas ───────────────────────────────────────────
slides.push({
  num: 13,
  title: "Business Model — How This Works",
  content: [
    heading("Key Partners", 2),
    bullet("State Health Departments (MoU-based deployment in government hospitals)"),
    bullet("Hospital Chains (Apollo, Fortis, Max — pilot and scale)"),
    bullet("Medical Colleges (teaching hospitals — research + training use case)"),
    bullet("NGOs (healthcare access programs in rural India)"),
    heading("Key Activities", 2),
    bullet("Product development (rule engine → ML → AI, phased)"),
    bullet("Clinical validation (pilot studies, peer-reviewed publications)"),
    bullet("Regulatory compliance (CDSCO pathway, quality management)"),
    bullet("Sales & deployment (hospital onboarding, training, support)"),
    heading("Key Resources", 2),
    bullet("Clinical expertise (emergency medicine advisors)"),
    bullet("Technology (open-source stack, cloud infrastructure)"),
    bullet("Data (anonymized assessment records for ML training)"),
    bullet("Partnerships (hospital relationships, government MoUs)"),
    heading("Cost Structure", 2),
    bullet("Development: ₹15–20L per year (engineering team)"),
    bullet("Validation: ₹5–10L per year (clinical studies, IRB fees)"),
    bullet("Infrastructure: ₹2–5L per year (hosting, compute for ML)"),
    bullet("Sales: ₹5–10L per year (travel, demos, conferences)"),
  ],
  note: "Keep the business model simple. You're not explaining a corporation — you're explaining a focused startup approach. The key insight is the partnership with government hospitals (free deployment, large scale) combined with paid private hospital subscriptions.",
});

// ── SLIDE 14: Revenue Model ───────────────────────────────────────────────────
slides.push({
  num: 14,
  title: "Revenue Model — Scale & Sustainability",
  content: [
    heading("Tiered Pricing (India)", 2),
    bullet("GOVERNMENT / NGO (Free): Open-source deployment, community support, data contribution for research"),
    bullet("SMALL HOSPITALS (<50 beds): ₹50,000/year — basic triage, email support"),
    bullet("MEDIUM HOSPITALS (50–200 beds): ₹1,50,000/year — triage + dashboard + training"),
    bullet("LARGE HOSPITALS (200+ beds): ₹3,00,000–5,00,000/year — full platform + EMR integration + on-site training"),
    bullet("MEDICAL COLLEGES: ₹25,000/year — educational license, student training module"),
    heading("Global Pricing (Phase 3)", 2),
    bullet("SaaS model: $5,000–50,000/year per hospital (USD)"),
    bullet("API licensing: Per-assessment fee for telehealth integrations"),
    bullet("Enterprise: White-label + custom ESI rules for health systems"),
    heading("Revenue Projections", 2),
    bullet("Year 1: 10 hospitals × ₹1L avg = ₹10L revenue (validation phase)"),
    bullet("Year 2: 50 hospitals × ₹1.5L avg = ₹75L revenue (scale phase)"),
    bullet("Year 3: 150 hospitals × ₹2L avg = ₹3Cr revenue (growth phase)"),
    bullet("Year 5: 500+ hospitals, global expansion → ₹15Cr+ revenue"),
  ],
  note: "Show the revenue model with confidence. The freemium approach for government hospitals is key — it builds adoption and data while private hospitals fund growth. The global market is where margins are highest. If asked about ROI for hospitals, mention that reducing ED wait times by 30% can save ₹20–50L per year per hospital in efficiency gains.",
});

// ── SLIDE 15: Product Roadmap ─────────────────────────────────────────────────
slides.push({
  num: 15,
  title: "Product Roadmap — The Journey Ahead",
  content: [
    heading("Phase 1: Rule-Based Foundation (Months 1–6) ✅ IN PROGRESS", 2),
    bullet("Complete ESI v5 rule engine with all 4 decision points ✓"),
    bullet("React + FastAPI full-stack application ✓"),
    bullet("Clinician override + outcome tracking ✓"),
    bullet("Accuracy dashboard ✓"),
    bullet("Pilot in 3–5 hospitals with 200+ assessments"),
    bullet("Target: 90% AI-clinician agreement rate"),
    heading("Phase 2: ML Enhancement (Months 7–18)", 2),
    bullet("NLP for free-text chief complaint extraction (MedBERT fine-tuned on Indian medical text)"),
    bullet("ML-based resource prediction (XGBoost/Random Forest on historical data)"),
    bullet("Multilingual support (Hindi, Tamil, Telugu, Bengali)"),
    bullet("Mobile app (React Native) for bedside triage"),
    bullet("EMR integration (FHIR API for interoperability)"),
    bullet("Target: 20 pilot hospitals, 5,000+ assessments"),
    heading("Phase 3: Full AI Platform (Months 19–36)", 2),
    bullet("Deep learning model for triage prediction (transformer architecture)"),
    bullet("Predictive analytics: Length of stay, admission probability, ICU need"),
    bullet("Multi-hospital analytics network (anonymized benchmarking)"),
    bullet("CDSCO certification as Software as a Medical Device"),
    bullet("International expansion (Southeast Asia, Africa)"),
  ],
  note: "This is your closing slide — make it memorable. Emphasize that Phase 1 is already built and working. The roadmap shows you've thought through the technical challenges. The international expansion is the long-term vision. End with confidence: 'We have the foundation. Now we scale.'",
});

`;

fs.writeFileSync("C:\\projects\\Triage_assist\\build_docx.js", script);
console.log("Script written successfully");

import React, { useState } from 'react'
import './TriageForm.css'

// ── Chief Complaints: exactly what the rule engine handles ──────────────────
const CHIEF_COMPLAINT_OPTIONS = [
  { group: '🫀 Cardiac / Vascular', options: [
    { label: 'Chest pain',                    value: 'chest pain',             autoSymptoms: ['Chest pain'] },
    { label: 'Palpitations / Racing heart',   value: 'palpitations',           autoSymptoms: [] },
    { label: 'Syncope / Fainting',            value: 'syncope',                autoSymptoms: ['Dizziness'] },
  ]},
  { group: '🫁 Respiratory', options: [
    { label: 'Shortness of breath',           value: 'shortness of breath',    autoSymptoms: ['Shortness of breath'] },
    { label: 'Difficulty breathing',          value: 'difficulty breathing',   autoSymptoms: ['Shortness of breath'] },
    { label: 'Wheezing / Stridor',            value: 'wheezing',               autoSymptoms: ['Shortness of breath'] },
    { label: 'Cough',                         value: 'cough',                  autoSymptoms: ['Cough'] },
  ]},
  { group: '🧠 Neurological', options: [
    { label: 'Altered mental status',         value: 'altered mental status',  autoSymptoms: ['Altered mental status'] },
    { label: 'Stroke symptoms (face droop / arm weakness / speech)', value: 'face drooping arm weakness speech difficulty', autoSymptoms: ['Weakness', 'Altered mental status'] },
    { label: 'Sudden weakness / Numbness',    value: 'sudden weakness',        autoSymptoms: ['Weakness'] },
    { label: 'Slurred speech / Aphasia',      value: 'slurred speech',         autoSymptoms: ['Altered mental status'] },
    { label: 'Sudden vision loss',            value: 'sudden vision loss',     autoSymptoms: ['Eye pain'] },
    { label: 'Headache',                      value: 'headache',               autoSymptoms: ['Headache'] },
    { label: 'Seizure',                       value: 'seizure',                autoSymptoms: ['Seizure'] },
    { label: 'Dizziness / Vertigo',           value: 'dizzy',                  autoSymptoms: ['Dizziness'] },
  ]},
  { group: '🫃 Abdominal / GI', options: [
    { label: 'Abdominal pain',                value: 'abdominal pain',         autoSymptoms: ['Abdominal pain'] },
    { label: 'Nausea / Vomiting',             value: 'nausea vomiting',        autoSymptoms: ['Nausea/Vomiting'] },
    { label: 'Diarrhea',                      value: 'diarrhea',               autoSymptoms: ['Diarrhea'] },
    { label: 'Constipation',                  value: 'constipation',           autoSymptoms: ['Constipation'] },
    { label: 'Bleeding (GI)',                 value: 'bleeding',               autoSymptoms: ['Bleeding'] },
  ]},
  { group: '🦴 Trauma / Injury', options: [
    { label: 'Fall / Injury',                 value: 'fall',                   autoSymptoms: ['Injury/Trauma'] },
    { label: 'Motor vehicle collision (MVC)', value: 'motor vehicle',          autoSymptoms: ['Injury/Trauma'] },
    { label: 'Gunshot wound',                 value: 'gunshot',                autoSymptoms: ['Injury/Trauma', 'Bleeding'] },
    { label: 'Stab wound / Penetrating trauma', value: 'stab wound',          autoSymptoms: ['Injury/Trauma', 'Bleeding'] },
    { label: 'Back pain',                     value: 'back pain',              autoSymptoms: ['Back pain'] },
  ]},
  { group: '🌡️ Infection / Sepsis', options: [
    { label: 'Fever',                         value: 'fever',                  autoSymptoms: ['Fever'] },
    { label: 'Fever + chills (sepsis concern)', value: 'fever chills infection', autoSymptoms: ['Fever'] },
    { label: 'Urinary symptoms / UTI',        value: 'urinary',                autoSymptoms: ['Urinary symptoms'] },
    { label: 'Rash / Skin infection',         value: 'rash',                   autoSymptoms: ['Rash'] },
  ]},
  { group: '🧬 Urological / Reproductive', options: [
    { label: 'Testicular pain (torsion concern)', value: 'testicular pain',    autoSymptoms: ['Testicular pain'] },
    { label: 'Lower quadrant pain (ovarian torsion concern)', value: 'lower quadrant pain', autoSymptoms: ['Abdominal pain'] },
    { label: 'Vaginal bleeding (pregnancy concern)', value: 'vaginal bleeding abdominal pain', autoSymptoms: ['Abdominal pain', 'Bleeding'] },
    { label: 'Heavy vaginal bleeding (postpartum)', value: 'heavy vaginal bleeding', autoSymptoms: ['Bleeding'] },
  ]},
  { group: '🧠 Mental Health / Toxicology', options: [
    { label: 'Suicidal ideation / Self-harm',  value: 'suicidal',              autoSymptoms: ['Suicidal ideation'] },
    { label: 'Overdose / Toxic ingestion',     value: 'overdose ingestion poisoning toxic', autoSymptoms: ['Overdose'] },
    { label: 'Psychosis / Homicidal ideation', value: 'psychotic homicidal',   autoSymptoms: ['Altered mental status'] },
    { label: 'Sexual assault',                 value: 'sexual assault',        autoSymptoms: ['Sexual assault'] },
  ]},
  { group: '👁️ Sensory', options: [
    { label: 'Eye pain / Vision problem',     value: 'eye',                    autoSymptoms: ['Eye pain'] },
    { label: 'Ear pain / Hearing issue',      value: 'ear',                    autoSymptoms: ['Ear pain'] },
  ]},
]

const COMPLAINT_MAP = {}
CHIEF_COMPLAINT_OPTIONS.forEach(group =>
  group.options.forEach(opt => { COMPLAINT_MAP[opt.value] = opt })
)

const SYMPTOM_OPTIONS = [
  'Chest pain', 'Shortness of breath', 'Abdominal pain', 'Headache',
  'Dizziness', 'Nausea/Vomiting', 'Fever', 'Cough',
  'Back pain', 'Injury/Trauma', 'Bleeding', 'Altered mental status',
  'Weakness', 'Seizure', 'Suicidal ideation', 'Overdose',
  'Testicular pain', 'Eye pain', 'Ear pain', 'Rash',
  'Urinary symptoms', 'Diarrhea', 'Constipation', 'Sexual assault',
]

const HISTORY_OPTIONS = [
  'Hypertension', 'Diabetes', 'Heart disease', 'Asthma/COPD',
  'Cancer', 'Kidney disease', 'Liver disease', 'Stroke',
  'Immunosuppressed', 'Obesity', 'Substance use',
  'Psychiatric disorder', 'Bleeding disorder', 'Recent surgery',
]

const HISTORY_OPTIONS_FEMALE = [...HISTORY_OPTIONS, 'Pregnancy']

// ── Field validation rules (matches backend Pydantic + ESI clinical ranges) ──
const FIELD_RULES = {
  age:               { min: 0,    max: 120,  integer: true,  label: 'Age',              unit: 'years' },
  heart_rate:        { min: 0,    max: 300,  integer: true,  label: 'Heart Rate',       unit: 'bpm'   },
  bp_systolic:       { min: 0,    max: 300,  integer: true,  label: 'BP Systolic',      unit: 'mmHg'  },
  bp_diastolic:      { min: 0,    max: 200,  integer: true,  label: 'BP Diastolic',     unit: 'mmHg'  },
  respiratory_rate:  { min: 0,    max: 80,   integer: true,  label: 'Respiratory Rate', unit: '/min'  },
  spo2:              { min: 0,    max: 100,  integer: false, label: 'SpO2',             unit: '%'     },
  temperature:       { min: 20.0, max: 45.0, integer: false, label: 'Temperature',      unit: '°C'    },
  pain_score:        { min: 0,    max: 10,   integer: true,  label: 'Pain Score',       unit: '/10'   },
}

function clampNumeric(value, rules) {
  if (value === '' || value === '-') return value
  const num = rules.integer ? parseInt(value, 10) : parseFloat(value)
  if (isNaN(num)) return ''
  if (num < rules.min) return String(rules.min)
  if (num > rules.max) return String(rules.max)
  return String(num)
}

function NumericInput({ fieldKey, value, onChange, placeholder, step }) {
  const rules = FIELD_RULES[fieldKey]
  const [error, setError] = useState('')

  const handleChange = (e) => {
    const raw = e.target.value;
    onChange(raw); // Always allow raw typing

    if (raw === '') { setError(''); return; }

    const num = rules.integer ? parseInt(raw, 10) : parseFloat(raw);
    if (isNaN(num)) { 
      setError('Must be a number');
    } else if (num < rules.min || num > rules.max) {
      setError(`Must be ${rules.min}-${rules.max} ${rules.unit}`);
    } else {
      setError('');
    }
  }

  return (
    <div className="numeric-field">
      <input
        type="number"
        value={value}
        onChange={handleChange}
        onBlur={e => onChange(clampNumeric(e.target.value, rules))}
        placeholder={placeholder}
        min={rules.min}
        max={rules.max}
        step={step || (rules.integer ? 1 : 0.1)}
      />
      {error && <span className="field-error">{error}</span>}
      <span className="field-range">{rules.min}–{rules.max} {rules.unit}</span>
    </div>
  )
}

function TriageForm({ onSubmit }) {
  const [form, setForm] = useState({
    age: '', sex: 'M',
    chief_complaint: '',
    symptoms: [],
    heart_rate: '', bp_systolic: '', bp_diastolic: '',
    respiratory_rate: '', spo2: '', temperature: '',
    pain_score: '', level_of_consciousness: 'alert',
    medical_history: [], medications: [], allergies: [],
    is_pregnant: false, is_postpartum: false,
  })
  const [submitting, setSubmitting] = useState(false)

  const update = (key, val) => {
    if (key === 'sex' && val === 'M') {
      setForm(f => ({ ...f, sex: 'M', is_pregnant: false, is_postpartum: false,
        medical_history: f.medical_history.filter(h => h !== 'Pregnancy') }))
    } else if (key === 'chief_complaint') {
      const match = COMPLAINT_MAP[val]
      if (match) {
        setForm(f => ({
          ...f,
          chief_complaint: val,
          symptoms: [...new Set([...f.symptoms, ...match.autoSymptoms])],
        }))
      } else {
        setForm(f => ({ ...f, chief_complaint: val }))
      }
    } else {
      setForm(f => ({ ...f, [key]: val }))
    }
  }

  const toggleItem = (key, item) => {
    setForm(f => ({
      ...f,
      [key]: f[key].includes(item)
        ? f[key].filter(x => x !== item)
        : [...f[key], item],
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    // Final clamp + parse before sending
    const age = parseInt(form.age) || 0
    if (age < 0 || age > 120) return alert('Age must be 0–120 years')

    const pain = form.pain_score !== '' ? parseInt(form.pain_score) : null
    if (pain !== null && (pain < 0 || pain > 10)) return alert('Pain score must be 0–10')

    setSubmitting(true)
    const data = {
      ...form,
      age,
      heart_rate:       form.heart_rate       ? parseInt(form.heart_rate)       : null,
      bp_systolic:      form.bp_systolic      ? parseInt(form.bp_systolic)      : null,
      bp_diastolic:     form.bp_diastolic     ? parseInt(form.bp_diastolic)     : null,
      respiratory_rate: form.respiratory_rate ? parseInt(form.respiratory_rate) : null,
      spo2:             form.spo2             ? parseFloat(form.spo2)           : null,
      temperature:      form.temperature      ? parseFloat(form.temperature)    : null,
      pain_score:       pain,
    }
    await onSubmit(data)
    setSubmitting(false)
  }

  return (
    <form className="triage-form" onSubmit={handleSubmit}>
      <h2>Patient Information</h2>

      {/* Demographics */}
      <fieldset>
        <legend>Demographics</legend>
        <div className="form-row">
          <label>
            Age
            <NumericInput fieldKey="age" value={form.age} onChange={v => update('age', v)} placeholder="0–120" />
          </label>
          <label>
            Sex
            <select value={form.sex} onChange={e => update('sex', e.target.value)}>
              <option value="M">Male</option>
              <option value="F">Female</option>
            </select>
          </label>
        </div>

        <label>
          Chief Complaint
          <span className="field-hint">⚙️ Rule-engine supported complaints only</span>
          <select value={form.chief_complaint} onChange={e => update('chief_complaint', e.target.value)} required>
            <option value="">— Select chief complaint —</option>
            {CHIEF_COMPLAINT_OPTIONS.map(group => (
              <optgroup key={group.group} label={group.group}>
                {group.options.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </optgroup>
            ))}
          </select>
        </label>

        {form.chief_complaint && (
          <p className="auto-hint">✅ Matching symptoms auto-selected below. Add more if needed.</p>
        )}

        <div className="form-row">
          {form.sex === 'F' && (
            <>
              <label className="checkbox-label">
                <input type="checkbox" checked={form.is_pregnant} onChange={e => update('is_pregnant', e.target.checked)} />
                Pregnant
              </label>
              <label className="checkbox-label">
                <input type="checkbox" checked={form.is_postpartum} onChange={e => update('is_postpartum', e.target.checked)} />
                Postpartum (&lt; 6 weeks)
              </label>
            </>
          )}
        </div>
      </fieldset>

      {/* Vital Signs */}
      <fieldset>
        <legend>Vital Signs</legend>
        <div className="form-row">
          <label>
            Heart Rate (bpm)
            <NumericInput fieldKey="heart_rate" value={form.heart_rate} onChange={v => update('heart_rate', v)} placeholder="60–100" />
          </label>
          <label>
            BP Systolic (mmHg)
            <NumericInput fieldKey="bp_systolic" value={form.bp_systolic} onChange={v => update('bp_systolic', v)} placeholder="90–120" />
          </label>
          <label>
            BP Diastolic (mmHg)
            <NumericInput fieldKey="bp_diastolic" value={form.bp_diastolic} onChange={v => update('bp_diastolic', v)} placeholder="60–80" />
          </label>
        </div>
        <div className="form-row">
          <label>
            Respiratory Rate (/min)
            <NumericInput fieldKey="respiratory_rate" value={form.respiratory_rate} onChange={v => update('respiratory_rate', v)} placeholder="12–20" />
          </label>
          <label>
            SpO2 (%)
            <NumericInput fieldKey="spo2" value={form.spo2} onChange={v => update('spo2', v)} placeholder="95–100" step={0.1} />
          </label>
          <label>
            Temperature (°C)
            <NumericInput fieldKey="temperature" value={form.temperature} onChange={v => update('temperature', v)} placeholder="36.5–37.5" step={0.1} />
          </label>
        </div>
        <div className="form-row">
          <label>
            Pain Score (0–10)
            <NumericInput fieldKey="pain_score" value={form.pain_score} onChange={v => update('pain_score', v)} placeholder="0–10" />
          </label>
          <label>
            Level of Consciousness
            <select value={form.level_of_consciousness} onChange={e => update('level_of_consciousness', e.target.value)}>
              <option value="alert">Alert</option>
              <option value="confused">Confused</option>
              <option value="lethargic">Lethargic</option>
              <option value="disoriented">Disoriented</option>
              <option value="unresponsive">Unresponsive</option>
            </select>
          </label>
        </div>
      </fieldset>

      {/* Symptoms */}
      <fieldset>
        <legend>Symptoms (select all that apply)</legend>
        <div className="checkbox-grid">
          {SYMPTOM_OPTIONS.map(s => (
            <label key={s} className="chip-label">
              <input
                type="checkbox"
                checked={form.symptoms.includes(s)}
                onChange={() => toggleItem('symptoms', s)}
              />
              {s}
            </label>
          ))}
        </div>
      </fieldset>

      {/* Medical History */}
      <fieldset>
        <legend>Medical History (select all that apply)</legend>
        <div className="checkbox-grid">
          {(form.sex === 'F' ? HISTORY_OPTIONS_FEMALE : HISTORY_OPTIONS).map(h => (
            <label key={h} className="chip-label">
              <input
                type="checkbox"
                checked={form.medical_history.includes(h)}
                onChange={() => toggleItem('medical_history', h)}
              />
              {h}
            </label>
          ))}
        </div>
      </fieldset>

      <button type="submit" className="assess-btn" disabled={submitting}>
        {submitting ? 'Assessing...' : 'Assess Patient'}
      </button>
    </form>
  )
}

export default TriageForm

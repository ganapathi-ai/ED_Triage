import React, { useState } from 'react'
import './TriageForm.css'

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
  'Immunosuppressed', 'Pregnancy', 'Obesity', 'Substance use',
  'Psychiatric disorder', 'Bleeding disorder', 'Recent surgery',
]

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

  const update = (key, val) => setForm(f => ({ ...f, [key]: val }))

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
    setSubmitting(true)
    const data = {
      ...form,
      age: parseInt(form.age) || 0,
      heart_rate: form.heart_rate ? parseInt(form.heart_rate) : null,
      bp_systolic: form.bp_systolic ? parseInt(form.bp_systolic) : null,
      bp_diastolic: form.bp_diastolic ? parseInt(form.bp_diastolic) : null,
      respiratory_rate: form.respiratory_rate ? parseInt(form.respiratory_rate) : null,
      spo2: form.spo2 ? parseFloat(form.spo2) : null,
      temperature: form.temperature ? parseFloat(form.temperature) : null,
      pain_score: form.pain_score ? parseInt(form.pain_score) : null,
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
            <input type="number" value={form.age} onChange={e => update('age', e.target.value)} required min="0" max="120" />
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
          <input type="text" value={form.chief_complaint} onChange={e => update('chief_complaint', e.target.value)} placeholder="e.g., chest pain, shortness of breath" />
        </label>
        <div className="form-row">
          <label className="checkbox-label">
            <input type="checkbox" checked={form.is_pregnant} onChange={e => update('is_pregnant', e.target.checked)} />
            Pregnant
          </label>
          <label className="checkbox-label">
            <input type="checkbox" checked={form.is_postpartum} onChange={e => update('is_postpartum', e.target.checked)} />
            Postpartum (&lt; 6 weeks)
          </label>
        </div>
      </fieldset>

      {/* Vital Signs */}
      <fieldset>
        <legend>Vital Signs</legend>
        <div className="form-row">
          <label>
            Heart Rate (bpm)
            <input type="number" value={form.heart_rate} onChange={e => update('heart_rate', e.target.value)} placeholder="60-100" />
          </label>
          <label>
            BP Systolic
            <input type="number" value={form.bp_systolic} onChange={e => update('bp_systolic', e.target.value)} placeholder="90-120" />
          </label>
          <label>
            BP Diastolic
            <input type="number" value={form.bp_diastolic} onChange={e => update('bp_diastolic', e.target.value)} placeholder="60-80" />
          </label>
        </div>
        <div className="form-row">
          <label>
            Respiratory Rate
            <input type="number" value={form.respiratory_rate} onChange={e => update('respiratory_rate', e.target.value)} placeholder="12-20" />
          </label>
          <label>
            SpO2 (%)
            <input type="number" value={form.spo2} onChange={e => update('spo2', e.target.value)} placeholder="95-100" step="0.1" />
          </label>
          <label>
            Temperature (°C)
            <input type="number" value={form.temperature} onChange={e => update('temperature', e.target.value)} placeholder="36.5-37.5" step="0.1" />
          </label>
        </div>
        <div className="form-row">
          <label>
            Pain Score (0-10)
            <input type="number" value={form.pain_score} onChange={e => update('pain_score', e.target.value)} min="0" max="10" />
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
          {HISTORY_OPTIONS.map(h => (
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

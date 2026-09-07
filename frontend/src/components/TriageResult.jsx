import React, { useState, useEffect } from 'react'
import './TriageResult.css'

const ESI_CONFIG = {
  1: { label: 'IMMEDIATE', color: '#dc2626', bg: '#fef2f2', description: 'Lifesaving intervention required' },
  2: { label: 'URGENT', color: '#ea580c', bg: '#fff7ed', description: 'High risk / Severe pain / Altered mental status' },
  3: { label: 'LESS URGENT', color: '#ca8a04', bg: '#fefce8', description: 'Stable, needs multiple resources' },
  4: { label: 'NON-URGENT', color: '#16a34a', bg: '#f0fdf4', description: 'Stable, needs one resource' },
  5: { label: 'MINIMAL', color: '#6b7280', bg: '#f9fafb', description: 'Stable, no resources beyond exam' },
}

function TriageResult({ result, onNew, apiBase }) {
  const [override, setOverride] = useState(null)
  const [overrideNote, setOverrideNote] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [showOutcome, setShowOutcome] = useState(false)

  const config = ESI_CONFIG[result.esi_level] || ESI_CONFIG[3]

  const handleOverride = async () => {
    try {
      await fetch(`${apiBase}/assessments/${result.id}/override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clinician_esi_level: parseInt(override),
          clinician_notes: overrideNote,
        }),
      })
      setSubmitted(true)
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="triage-result">
      <button className="back-btn" onClick={onNew}>← New Assessment</button>

      <div className="result-card" style={{ borderColor: config.color, backgroundColor: config.bg }}>
        <div className="result-header">
          <div className="level-badge" style={{ backgroundColor: config.color, color: '#fff' }}>
            ESI {result.esi_level}
          </div>
          <div className="level-info">
            <h2 style={{ color: config.color }}>{config.label}</h2>
            <p className="risk-label">Risk Level: <strong>{result.risk}</strong></p>
            <p className="description">{config.description}</p>
          </div>
        </div>

        {result.reasons.length > 0 && (
          <div className="result-section">
            <h3>Key Findings</h3>
            <ul>
              {result.reasons.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          </div>
        )}

        {result.warnings.length > 0 && (
          <div className="result-section warnings">
            <h3>Warnings</h3>
            <ul>
              {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </div>
        )}

        <div className="result-section recommendation">
          <h3>Recommendation</h3>
          <p>{result.recommendation}</p>
        </div>
      </div>

      {/* Clinician Override */}
      <div className="override-section">
        <h3>Clinician Override</h3>
        {!submitted ? (
          <>
            <div className="form-row">
              <label>
                Override to ESI Level:
                <select value={override || ''} onChange={e => setOverride(e.target.value)}>
                  <option value="">— Select —</option>
                  {[1,2,3,4,5].map(l => (
                    <option key={l} value={l}>ESI {l} — {ESI_CONFIG[l].label}</option>
                  ))}
                </select>
              </label>
              <label>
                Notes:
                <input type="text" value={overrideNote} onChange={e => setOverrideNote(e.target.value)} placeholder="Reason for override..." />
              </label>
            </div>
            <button className="override-btn" onClick={handleOverride} disabled={!override}>
              Record Override
            </button>
          </>
        ) : (
          <p className="success-msg">Override recorded — ESI {override} (clinician decision)</p>
        )}
      </div>
    </div>
  )
}

export default TriageResult

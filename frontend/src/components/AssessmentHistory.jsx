import React, { useState, useEffect } from 'react'
import './AssessmentHistory.css'

function AssessmentHistory({ apiBase }) {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    fetch(`${apiBase}/assessments?limit=50`)
      .then(r => r.json())
      .then(data => { setRecords(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [apiBase])

  const loadDetail = async (id) => {
    const res = await fetch(`${apiBase}/assessments/${id}`)
    const data = await res.json()
    setSelected(data)
  }

  if (loading) return <p className="loading">Loading assessments...</p>

  return (
    <div className="history">
      <h2>Assessment History ({records.length} records)</h2>
      <div className="history-layout">
        <table className="history-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Date</th>
              <th>Age</th>
              <th>Symptoms</th>
              <th>System ESI</th>
              <th>Clinician ESI</th>
              <th>Risk</th>
                          </tr>
          </thead>
          <tbody>
            {records.map(r => (
              <tr key={r.id} onClick={() => loadDetail(r.id)} className={selected?.id === r.id ? 'selected' : ''}>
                <td>{r.id}</td>
                <td>{new Date(r.created_at).toLocaleString()}</td>
                <td>{r.age}</td>
                <td className="symptoms-cell">{r.symptoms.slice(0, 2).join(', ')}{r.symptoms.length > 2 ? '...' : ''}</td>
                <td><span className={`esi-badge esi-${r.ai_esi_level}`}>{r.ai_esi_level}</span></td>
                <td>{r.clinician_esi_level || '—'}</td>
                <td><span className={`risk-badge risk-${r.ai_risk?.toLowerCase()}`}>{r.ai_risk}</span></td>
                              </tr>
            ))}
          </tbody>
        </table>

        {selected && (
          <div className="detail-panel">
            <h3>Assessment #{selected.id}</h3>
            <div className="detail-grid">
              <div><strong>Age/Sex:</strong> {selected.age} / {selected.sex}</div>
              <div><strong>Chief Complaint:</strong> {selected.chief_complaint}</div>
              <div><strong>Symptoms:</strong> {selected.symptoms.join(', ')}</div>
              <div><strong>HR:</strong> {selected.heart_rate} | <strong>BP:</strong> {selected.bp_systolic}/{selected.bp_diastolic}</div>
              <div><strong>RR:</strong> {selected.respiratory_rate} | <strong>SpO2:</strong> {selected.spo2}%</div>
              <div><strong>Temp:</strong> {selected.temperature}°C | <strong>Pain:</strong> {selected.pain_score}/10</div>
              <div><strong>LOC:</strong> {selected.level_of_consciousness}</div>
              <div><strong>History:</strong> {selected.medical_history.join(', ') || 'None'}</div>
              <div><strong>Meds:</strong> {selected.medications.join(', ') || 'None'}</div>
              <div><strong>Allergies:</strong> {selected.allergies.join(', ') || 'None'}</div>
              <div><strong>System ESI:</strong> <span className={`esi-badge esi-${selected.ai_esi_level}`}>{selected.ai_esi_level}</span></div>
              <div><strong>Clinician ESI:</strong> {selected.clinician_esi_level || 'Not recorded'}</div>
                            <div className="full-width"><strong>System Reasons:</strong> {selected.ai_reasons?.join(', ')}</div>
              {selected.clinician_notes && <div className="full-width"><strong>Clinician Notes:</strong> {selected.clinician_notes}</div>}
                          </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AssessmentHistory

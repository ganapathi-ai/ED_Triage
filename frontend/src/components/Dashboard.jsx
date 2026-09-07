import React, { useState, useEffect } from 'react'
import './Dashboard.css'

function Dashboard({ apiBase }) {
  const [metrics, setMetrics] = useState(null)

  useEffect(() => {
    fetch(`${apiBase}/dashboard`)
      .then(r => r.json())
      .then(setMetrics)
  }, [apiBase])

  if (!metrics) return <p>Loading dashboard...</p>

  return (
    <div className="dashboard">
      <h2>Dashboard</h2>
      <div className="metrics-grid">
        <div className="metric-card">
          <h3>Total Assessments</h3>
          <p className="metric-value">{metrics.total_assessments}</p>
        </div>
        <div className="metric-card high-risk">
          <h3>High Risk</h3>
          <p className="metric-value">{metrics.high_risk_count}</p>
        </div>
        <div className="metric-card medium-risk">
          <h3>Medium Risk</h3>
          <p className="metric-value">{metrics.medium_risk_count}</p>
        </div>
        <div className="metric-card low-risk">
          <h3>Low Risk</h3>
          <p className="metric-value">{metrics.low_risk_count}</p>
        </div>
      </div>

      <div className="accuracy-metrics">
        <h3>System Accuracy Metrics (vs Clinician)</h3>
        {metrics.total_assessments === 0 ? (
          <p>No clinician overrides recorded yet. Override assessments to see agreement rates.</p>
        ) : (
          <>
            <div className="accuracy-item">
              <span>Agreement Rate</span>
              <div className="bar-container">
                <div className="bar agreement" style={{ width: `${metrics.ai_clinician_agreement}%` }} />
              </div>
              <span>{metrics.ai_clinician_agreement}%</span>
            </div>
            <div className="accuracy-item">
              <span>Under-triage Rate (System rated lower than clinician)</span>
              <div className="bar-container">
                <div className="bar under" style={{ width: `${metrics.under_triage_rate}%` }} />
              </div>
              <span>{metrics.under_triage_rate}%</span>
            </div>
            <div className="accuracy-item">
              <span>Over-triage Rate (System rated higher than clinician)</span>
              <div className="bar-container">
                <div className="bar over" style={{ width: `${metrics.over_triage_rate}%` }} />
              </div>
              <span>{metrics.over_triage_rate}%</span>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default Dashboard

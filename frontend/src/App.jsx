import React, { useState } from 'react'
import TriageForm from './components/TriageForm'
import TriageResult from './components/TriageResult'
import AssessmentHistory from './components/AssessmentHistory'
import Dashboard from './components/Dashboard'
import './App.css'

const API_BASE = ''

function App() {
  const [view, setView] = useState('form') // 'form' | 'history' | 'dashboard'
  const [lastResult, setLastResult] = useState(null)

  const handleAssess = async (data) => {
    try {
      const res = await fetch(`${API_BASE}/triage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('Triage request failed')
      const result = await res.json()
      setLastResult(result)
      setView('result')
    } catch (err) {
      console.error(err)
      alert('Error: ' + err.message)
    }
  }

  const handleNewAssessment = () => {
    setLastResult(null)
    setView('form')
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>ED Triage Assistant</h1>
          <p className="subtitle">ESI v5-based triage decision support</p>
        </div>
        <nav className="nav-tabs">
          <button
            className={view === 'form' ? 'active' : ''}
            onClick={() => setView('form')}
          >
            New Assessment
          </button>
          <button
            className={view === 'history' ? 'active' : ''}
            onClick={() => setView('history')}
          >
            History
          </button>
          <button
            className={view === 'dashboard' ? 'active' : ''}
            onClick={() => setView('dashboard')}
          >
            Dashboard
          </button>
        </nav>
      </header>

      <main className="app-main">
        {view === 'form' && (
          <TriageForm onSubmit={handleAssess} />
        )}
        {view === 'result' && lastResult && (
          <TriageResult
            result={lastResult}
            onNew={handleNewAssessment}
            apiBase={API_BASE}
          />
        )}
        {view === 'history' && (
          <AssessmentHistory apiBase={API_BASE} />
        )}
        {view === 'dashboard' && (
          <Dashboard apiBase={API_BASE} />
        )}
      </main>

      <footer className="app-footer">
        <p>Decision support only — does not replace clinical judgment.</p>
        <p>Based on ESI v5 (Emergency Nurses Association, 2023).</p>
      </footer>
    </div>
  )
}

export default App

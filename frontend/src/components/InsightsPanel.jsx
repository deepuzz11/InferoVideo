import React, { useEffect, useState } from 'react'
import { useStore } from '../store'
import { getInsights } from '../services/api'
import Loader from './Loader'

export default function InsightsPanel() {
  const job = useStore(s => s.job)
  const [insights, setInsights] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!job?.job_id || job.insights_status !== 'done') return
    setLoading(true)
    getInsights(job.job_id)
      .then(r => setInsights(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [job?.job_id, job?.insights_status])

  if (job?.insights_status === 'running' || job?.insights_status === 'pending') {
    return (
      <div className="empty">
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 12 }}>
          <Loader stage="insights" status="running" />
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-2)' }}>Extracting key insights…</div>
      </div>
    )
  }

  if (!insights || (!insights.entities.length && !insights.keywords.length)) {
    return (
      <div className="empty">
        <div className="empty-icon">💡</div>
        <div>No significant insights found yet</div>
      </div>
    )
  }

  // Calculate entity distribution
  const entityCounts = insights.entities.reduce((acc, ent) => {
    acc[ent.label] = (acc[ent.label] || 0) + 1
    return acc
  }, {})

  const sortedEntityLabels = Object.keys(entityCounts).sort((a, b) => entityCounts[b] - entityCounts[a])
  const maxCount = Math.max(...Object.values(entityCounts))
  
  const labelColors = {
    PERSON: '#4dabf7',
    ORG: '#be4bdb',
    GPE: '#51cf66',
    PRODUCT: '#ff922b',
    EVENT: '#fab005'
  }

  return (
    <div className="insights-grid">
      {/* 1. Entity Distribution Viz */}
      {sortedEntityLabels.length > 0 && (
        <div className="viz-container glass fade-in-up stagger-1">
          <div className="label" style={{ marginBottom: 16 }}>Entity Distribution</div>
          {sortedEntityLabels.map(label => (
            <div key={label} className="viz-bar-row">
              <div className="viz-bar-label">{label}</div>
              <div className="viz-bar-track">
                <div 
                  className="viz-bar-fill" 
                  style={{ 
                    width: `${(entityCounts[label] / maxCount) * 100}%`,
                    backgroundColor: labelColors[label] || 'var(--accent)'
                  }}
                />
                <div className="viz-bar-count">{entityCounts[label]}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 2. Named Entities List */}
      {insights.entities.length > 0 && (
        <div className="section fade-in-up stagger-2">
          <div className="label" style={{ marginBottom: 16 }}>Detected Entities</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {insights.entities.map((ent, i) => (
              <div key={i} className={`insight-pill ${ent.label}`}>
                <span className="ent-label">{ent.label}</span>
                <span className="ent-text">{ent.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Keywords Grid */}
      {insights.keywords.length > 0 && (
        <div className="section fade-in-up stagger-3">
          <div className="label" style={{ marginBottom: 16 }}>Key Topics & Themes</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 12 }}>
            {insights.keywords.map((kw, i) => (
              <div key={i} className="insight-card kw glass">
                <div className="kw-text">{kw.text}</div>
                <div className="kw-bar-wrap">
                  <div 
                    className="kw-bar-fill" 
                    style={{ width: `${Math.min(100, (kw.score / insights.keywords[0].score) * 100)}%` }} 
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

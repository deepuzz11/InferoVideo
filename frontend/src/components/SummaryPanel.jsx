import React, { useEffect } from 'react'
import { useStore } from '../store'
import { getSummary } from '../services/api'
import { useFormatTime } from '../hooks/useJobPoller'

export default function SummaryPanel({ onSeek }) {
  const job = useStore(s => s.job)
  const summary = useStore(s => s.summary)
  const setSummary = useStore(s => s.setSummary)
  const fmt = useFormatTime

  useEffect(() => {
    if (!job?.job_id || job.summarise_status !== 'done') return
    getSummary(job.job_id)
      .then(r => setSummary(r.data))
      .catch(() => {})
  }, [job?.job_id, job?.summarise_status])

  if (job?.summarise_status === 'running' || job?.summarise_status === 'pending') {
    return (
      <div className="empty">
        <div className="dots" style={{ justifyContent: 'center', marginBottom: 8 }}>
          <div className="dot"/><div className="dot"/><div className="dot"/>
        </div>
        <div>Generating summary…</div>
      </div>
    )
  }

  if (!summary) {
    return (
      <div className="empty">
        <div className="empty-icon">📝</div>
        <div>No summary yet</div>
      </div>
    )
  }

  return (
    <div className="fade-in">
      {/* Overall summary */}
      <div style={{ marginBottom: 20 }}>
        <div className="label" style={{ marginBottom: 10 }}>Overall Summary</div>
        <div
          style={{
            padding: '16px 20px',
            borderRadius: 'var(--radius)',
            background: 'var(--bg-2)',
            border: '1px solid var(--border)',
            borderLeft: '3px solid var(--accent)',
          }}
        >
          <p className="summary-text">{summary.overall}</p>
        </div>
      </div>

      {/* Per-chapter summaries */}
      {summary.chapters?.length > 0 && (
        <div>
          <div className="label" style={{ marginBottom: 12 }}>Chapter Summaries</div>
          {summary.chapters.map((ch, i) => (
            <div key={i} className="summary-chapter">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                <div className="summary-chapter-title">{ch.title}</div>
                <span
                  className="ts"
                  style={{ cursor: 'pointer' }}
                  onClick={() => onSeek?.(ch.start)}
                >
                  {fmt(ch.start)}
                </span>
              </div>
              <div className="summary-chapter-text">{ch.summary}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

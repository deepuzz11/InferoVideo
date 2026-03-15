import React from 'react'
import { useStore } from '../store'
import { useFormatTime } from '../hooks/useJobPoller'

const STAGES = [
  { key: 'ingest',     label: 'INGEST' },
  { key: 'transcribe', label: 'TRANSCRIBE' },
  { key: 'segment',    label: 'SEGMENT' },
  { key: 'highlight',  label: 'HIGHLIGHT' },
  { key: 'summarise',  label: 'SUMMARISE' },
]

function StagePill({ status, label }) {
  const icons = { pending: '○', running: '◉', done: '●', failed: '✗', skipped: '–' }
  return (
    <span className={`stage-pill ${status}`}>
      <span>{icons[status] || '○'}</span>
      {label}
    </span>
  )
}

export default function JobStatus() {
  const job = useStore(s => s.job)
  const fmt = useFormatTime

  if (!job) return null

  const isProcessing = job.overall_status === 'processing'
  const duration = job.meta?.duration_seconds

  return (
    <div className="card fade-in" style={{ marginBottom: 16 }}>
      <div className="card-inner">
        {/* Header row */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {job.meta?.title || 'Processing video…'}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="label" style={{ fontFamily: 'var(--font-mono)', fontSize: 10 }}>
                {job.job_id.slice(0, 8)}…
              </span>
              {duration && (
                <span className="tag">{fmt(duration)}</span>
              )}
              {job.meta?.segment_count && (
                <span className="tag">{job.meta.segment_count} segs</span>
              )}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0, marginLeft: 12 }}>
            {isProcessing && <div className="waveform">{[1,2,3,4,5,6].map(i => <div key={i} className="wave-bar" />)}</div>}
            <span className={`tag ${job.overall_status === 'complete' ? 'teal' : job.overall_status === 'failed' ? 'red' : 'accent'}`}>
              {job.overall_status.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Progress bar */}
        <div style={{ marginBottom: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <span className="label">Pipeline Progress</span>
            <span className="label" style={{ color: 'var(--accent)' }}>{job.progress_pct}%</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${job.progress_pct}%` }} />
          </div>
        </div>

        {/* Stage pills */}
        <div className="stage-row">
          {STAGES.map(s => (
            <StagePill
              key={s.key}
              status={job[`${s.key}_status`] || 'pending'}
              label={s.label}
            />
          ))}
        </div>

        {/* Error */}
        {job.error && (
          <div style={{ marginTop: 12, padding: '8px 12px', borderRadius: 8, background: 'rgba(255,107,74,0.08)', border: '1px solid rgba(255,107,74,0.2)', fontSize: 12, color: 'var(--accent-3)' }}>
            ✗ [{job.error_stage}] {job.error}
          </div>
        )}

        {/* Stats row */}
        {job.overall_status === 'complete' && (
          <div style={{ marginTop: 12, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            {job.meta?.chapter_count != null && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--accent)' }}>{job.meta.chapter_count}</div>
                <div className="label">Chapters</div>
              </div>
            )}
            {job.meta?.highlight_count != null && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--accent-2)' }}>{job.meta.highlight_count}</div>
                <div className="label">Highlights</div>
              </div>
            )}
            {job.meta?.segment_count != null && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--text)' }}>{job.meta.segment_count}</div>
                <div className="label">Segments</div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

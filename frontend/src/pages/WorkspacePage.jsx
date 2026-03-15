import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useStore } from '../store'
import { useJobPoller } from '../hooks/useJobPoller'
import VideoPlayer from '../components/VideoPlayer'
import JobStatus from '../components/JobStatus'
import ChaptersPanel from '../components/ChaptersPanel'
import SearchPanel from '../components/SearchPanel'
import HighlightsPanel from '../components/HighlightsPanel'
import SummaryPanel from '../components/SummaryPanel'
import InsightsPanel from '../components/InsightsPanel'
import { getJob } from '../services/api'

const TABS = [
  { id: 'chapters',   label: '📑 Chapters' },
  { id: 'search',     label: '🔍 Search' },
  { id: 'highlights', label: '✨ Highlights' },
  { id: 'summary',    label: '📝 Summary' },
  { id: 'insights',   label: '💡 Insights' },
]

export default function WorkspacePage() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const setJob = useStore(s => s.setJob)
  const activeTab = useStore(s => s.activeTab)
  const setActiveTab = useStore(s => s.setActiveTab)
  const reset = useStore(s => s.reset)
  const addToast = useStore(s => s.addToast)
  const [seekTo, setSeekTo] = useState(null)
  const [notFound, setNotFound] = useState(false)

  // Load job once on mount
  useEffect(() => {
    reset()
    getJob(jobId)
      .then(r => setJob(r.data))
      .catch(() => setNotFound(true))
  }, [jobId])

  // Poll while processing
  useJobPoller(jobId)

  const handleSeek = (t) => {
    setSeekTo(t)
    setTimeout(() => setSeekTo(null), 100)
  }

  if (notFound) {
    return (
      <div className="empty" style={{ paddingTop: 80 }}>
        <div className="empty-icon">🕳</div>
        <div style={{ fontSize: 15, marginBottom: 12 }}>Job not found</div>
        <button className="btn btn-primary" onClick={() => navigate('/')}>Go Home</button>
      </div>
    )
  }

  return (
    <div style={{ paddingTop: 20, paddingBottom: 40 }}>
      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/')}>← Home</button>
        <span style={{ color: 'var(--text-3)' }}>/</span>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/jobs')}>Jobs</button>
        <span style={{ color: 'var(--text-3)' }}>/</span>
        <span className="label" style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
          {jobId.slice(0, 12)}…
        </span>
      </div>

      {/* Job status bar */}
      <JobStatus />

      {/* Main layout */}
      <div className="layout">
        {/* Left sidebar */}
        <div>
          {/* Video player */}
          <VideoPlayer seekTo={seekTo} />

          {/* Sidebar tabs */}
          <div className="card">
            <div className="card-inner">
              <div className="tabs" style={{ marginBottom: 16 }}>
                {TABS.map(tab => (
                  <button
                    key={tab.id}
                    className={`tab${activeTab === tab.id ? ' active' : ''}`}
                    onClick={() => setActiveTab(tab.id)}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              <div style={{ minHeight: 200 }}>
                {activeTab === 'chapters'   && <div className="card-inner fade-in-up" key={activeTab}><ChaptersPanel   onSeek={handleSeek} /></div>}
                {activeTab === 'search'     && <div className="card-inner fade-in-up" key={activeTab}><SearchPanel     onSeek={handleSeek} /></div>}
                {activeTab === 'highlights' && <div className="card-inner fade-in-up" key={activeTab}><HighlightsPanel /></div>}
                {activeTab === 'summary'    && <div className="card-inner fade-in-up" key={activeTab}><SummaryPanel    onSeek={handleSeek} /></div>}
                {activeTab === 'insights'   && <div className="card-inner fade-in-up" key={activeTab}><InsightsPanel /></div>}
              </div>
            </div>
          </div>
        </div>

        {/* Right main area — transcript / info */}
        <div className="layout-main">
          <TranscriptSection jobId={jobId} onSeek={handleSeek} />
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Inline transcript viewer
// ---------------------------------------------------------------------------
import { getJob as _getJob } from '../services/api'
import { useFormatTime } from '../hooks/useJobPoller'

function TranscriptSection({ jobId, onSeek }) {
  const job = useStore(s => s.job)
  const fmt = useFormatTime
  const [segments, setSegments] = useState([])
  const [filterQ, setFilterQ] = useState('')
  const videoTime = useStore(s => s.videoTime)

  useEffect(() => {
    if (!job?.transcript_path || job.transcribe_status !== 'done') return
    // Fetch transcript JSON directly via static file server
    fetch(`/data/transcripts/${jobId}.json`)
      .then(r => r.json())
      .then(setSegments)
      .catch(() => {})
  }, [jobId, job?.transcribe_status])

  const filtered = filterQ.trim()
    ? segments.filter(s => s.text.toLowerCase().includes(filterQ.toLowerCase()))
    : segments

  return (
    <div>
      {/* Transcript */}
      <div className="card">
        <div className="card-inner">
          <div className="section-head">
            <span className="section-title">Full Transcript</span>
            {segments.length > 0 && (
              <span className="tag teal">{segments.length} segments</span>
            )}
          </div>

          {job?.transcribe_status === 'running' && (
            <div className="empty">
              <div className="dots" style={{ justifyContent: 'center', marginBottom: 8 }}>
                <div className="dot"/><div className="dot"/><div className="dot"/>
              </div>
              <div>Transcribing audio with Whisper…</div>
              <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 4 }}>This may take several minutes</div>
            </div>
          )}

          {job?.transcribe_status === 'pending' && job?.ingest_status !== 'done' && (
            <div className="empty">
              <div className="spinner" style={{ margin: '0 auto 10px' }} />
              <div>Downloading video…</div>
            </div>
          )}

          {job?.transcribe_status === 'pending' && job?.ingest_status === 'done' && (
            <div className="empty">
              <div className="spinner" style={{ margin: '0 auto 10px' }} />
              <div>Queued for transcription…</div>
            </div>
          )}

          {segments.length > 0 && (
            <>
              <div className="input-wrap" style={{ marginBottom: 14 }}>
                <span className="input-icon">
                  <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                  </svg>
                </span>
                <input
                  className="input has-icon"
                  style={{ fontSize: 12 }}
                  value={filterQ}
                  onChange={e => setFilterQ(e.target.value)}
                  placeholder="Filter transcript…"
                />
              </div>

              <div style={{ maxHeight: 520, overflowY: 'auto', paddingRight: 4 }}>
                {filtered.map((seg, i) => {
                  const isActive = videoTime >= seg.start && videoTime < seg.end
                  return (
                    <div
                      key={seg.id ?? i}
                      onClick={() => onSeek?.(seg.start)}
                      style={{
                        display: 'flex', gap: 10, padding: '7px 8px',
                        borderRadius: 8, cursor: 'pointer', transition: 'background 0.12s',
                        background: isActive ? 'rgba(232,255,71,0.06)' : 'transparent',
                        borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
                        marginBottom: 2,
                      }}
                      onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = 'var(--bg-2)' }}
                      onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = 'transparent' }}
                    >
                      <span
                        className="ts"
                        style={{ flexShrink: 0, fontSize: 10, marginTop: 2 }}
                        onClick={e => { e.stopPropagation(); onSeek?.(seg.start) }}
                      >
                        {fmt(seg.start)}
                      </span>
                      <span style={{ fontSize: 13, color: isActive ? 'var(--text)' : 'var(--text-2)', lineHeight: 1.5 }}>
                        {seg.text}
                      </span>
                    </div>
                  )
                })}
                {filtered.length === 0 && filterQ && (
                  <div className="empty"><div>No matches for "{filterQ}"</div></div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Metadata card */}
      {job?.overall_status === 'complete' && (
        <div className="card fade-in" style={{ marginTop: 16 }}>
          <div className="card-inner">
            <div className="section-head" style={{ marginBottom: 12 }}>
              <span className="section-title">Job Details</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              {[
                { label: 'Job ID',    value: job.job_id },
                { label: 'Source',    value: job.meta?.source_url ? '↗ URL' : '—' },
                { label: 'Duration',  value: job.meta?.duration_seconds ? fmt(job.meta.duration_seconds) : '—' },
                { label: 'Segments',  value: job.meta?.segment_count ?? '—' },
                { label: 'Chapters',  value: job.meta?.chapter_count  ?? '—' },
                { label: 'Highlights',value: job.meta?.highlight_count ?? '—' },
              ].map(row => (
                <div key={row.label} style={{ padding: '8px 12px', background: 'var(--bg-2)', borderRadius: 8, border: '1px solid var(--border)' }}>
                  <div className="label" style={{ marginBottom: 2 }}>{row.label}</div>
                  <div style={{ fontSize: 13, fontWeight: 600, fontFamily: 'var(--font-mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {row.label === 'Job ID' ? <span style={{ fontSize: 10 }}>{row.value}</span> :
                     row.label === 'Source' && job.meta?.source_url ? (
                       <a href={job.meta.source_url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-2)', textDecoration: 'none' }}>
                         {row.value}
                       </a>
                     ) : row.value}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

import React, { useEffect, useRef } from 'react'
import { useStore } from '../store'
import { getHighlights } from '../services/api'
import Loader from './Loader'

export default function HighlightsPanel() {
  const job = useStore(s => s.job)
  const highlights = useStore(s => s.highlights)
  const setHighlights = useStore(s => s.setHighlights)
  const videoRef = useRef(null)

  useEffect(() => {
    if (!job?.job_id || job.highlight_status !== 'done') return
    getHighlights(job.job_id)
      .then(r => setHighlights(r.data.clips))
      .catch(() => {})
  }, [job?.job_id, job?.highlight_status])

  const playClip = (url) => {
    // Find the main video element and swap src
    const v = document.querySelector('video')
    if (v) { v.src = url; v.play().catch(() => {}) }
  }

  if (job?.highlight_status === 'running' || job?.highlight_status === 'pending') {
    return (
      <div className="empty">
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 12 }}>
          <Loader stage="highlight" status="running" />
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-2)' }}>Extracting highlights…</div>
      </div>
    )
  }

  if (!highlights.length) {
    return (
      <div className="empty">
        <div className="empty-icon">✨</div>
        <div>No highlights yet</div>
      </div>
    )
  }
  return (
    <div className="fade-in-up">
      <div className="label stagger-1" style={{ marginBottom: 12 }}>
        {highlights.length} clip{highlights.length !== 1 ? 's' : ''} extracted
      </div>
      {highlights.map((clip, i) => (
        <div
          key={i}
          className={`clip-item glass fade-in-up stagger-${Math.min(5, i + 1)}`}
          onClick={() => playClip(clip.url)}
        >
          <div className="clip-thumb">
            <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z"/>
            </svg>
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="clip-title">Highlight {clip.index}</div>
            <div className="clip-meta">{clip.filename}</div>
          </div>
          <span className="tag accent">▶</span>
        </div>
      ))}
    </div>
  )
}

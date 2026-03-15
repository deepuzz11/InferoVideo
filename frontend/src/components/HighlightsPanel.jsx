import React, { useEffect, useRef } from 'react'
import { useStore } from '../store'
import { getHighlights } from '../services/api'

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
        <div className="dots" style={{ justifyContent: 'center', marginBottom: 8 }}>
          <div className="dot"/><div className="dot"/><div className="dot"/>
        </div>
        <div>Extracting highlights…</div>
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
    <div className="fade-in">
      <div style={{ marginBottom: 10, fontSize: 12, color: 'var(--text-3)' }}>
        {highlights.length} clip{highlights.length !== 1 ? 's' : ''} extracted · click to play
      </div>
      {highlights.map((clip, i) => (
        <div
          key={i}
          className="clip-item"
          style={{ animationDelay: `${i * 0.05}s` }}
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

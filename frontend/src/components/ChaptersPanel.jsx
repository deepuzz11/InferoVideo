import React, { useEffect } from 'react'
import { useStore } from '../store'
import { getChapters } from '../services/api'
import { useFormatTime } from '../hooks/useJobPoller'

export default function ChaptersPanel({ onSeek }) {
  const job = useStore(s => s.job)
  const chapters = useStore(s => s.chapters)
  const setChapters = useStore(s => s.setChapters)
  const activeChapter = useStore(s => s.activeChapter)
  const fmt = useFormatTime

  useEffect(() => {
    if (!job?.job_id || job.segment_status !== 'done') return
    getChapters(job.job_id)
      .then(r => setChapters(r.data.chapters))
      .catch(() => {})
  }, [job?.job_id, job?.segment_status])

  if (job?.segment_status === 'running' || job?.segment_status === 'pending') {
    return (
      <div className="empty">
        <div className="dots" style={{ justifyContent: 'center', marginBottom: 8 }}>
          <div className="dot"/><div className="dot"/><div className="dot"/>
        </div>
        <div>Segmenting chapters…</div>
      </div>
    )
  }

  if (!chapters.length) {
    return (
      <div className="empty">
        <div className="empty-icon">📑</div>
        <div>No chapters yet</div>
      </div>
    )
  }

  return (
    <div className="fade-in">
      {chapters.map((ch, i) => {
        const isActive = activeChapter?.start === ch.start
        return (
          <div
            key={i}
            className={`chapter-item${isActive ? ' active' : ''}`}
            onClick={() => onSeek?.(ch.start)}
          >
            <div className="chapter-title">{ch.title}</div>
            <div className="chapter-meta">
              <span className="chapter-num">CH {String(i + 1).padStart(2, '0')}</span>
              <div style={{ display: 'flex', gap: 6 }}>
                <span className="ts" onClick={e => { e.stopPropagation(); onSeek?.(ch.start) }}>
                  {fmt(ch.start)}
                </span>
                <span style={{ fontSize: 10, color: 'var(--text-3)', fontFamily: 'var(--font-mono)' }}>
                  {ch.segment_count} segs
                </span>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

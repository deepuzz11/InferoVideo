import React, { useRef, useEffect, useCallback } from 'react'
import { useStore } from '../store'
import { useFormatTime } from '../hooks/useJobPoller'

export default function VideoPlayer({ seekTo, onSeek }) {
  const videoRef = useRef(null)
  const job = useStore(s => s.job)
  const chapters = useStore(s => s.chapters)
  const setVideoTime = useStore(s => s.setVideoTime)
  const setActiveChapter = useStore(s => s.setActiveChapter)
  const fmt = useFormatTime

  // Expose seekTo externally
  useEffect(() => {
    if (seekTo != null && videoRef.current) {
      videoRef.current.currentTime = seekTo
      videoRef.current.play().catch(() => {})
    }
  }, [seekTo])

  const handleTimeUpdate = useCallback(() => {
    const t = videoRef.current?.currentTime || 0
    setVideoTime(t)
    // Update active chapter
    const active = chapters.findLast?.(ch => ch.start <= t) ?? null
    setActiveChapter(active)
  }, [chapters, setVideoTime, setActiveChapter])

  const videoSrc = job?.job_id
    ? `/data/videos/${job.job_id}.mp4`
    : null

  if (!videoSrc) {
    return (
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{
          aspectRatio: '16/9', display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          background: 'var(--bg-2)', borderRadius: 'var(--radius-lg)',
          color: 'var(--text-3)', gap: 12
        }}>
          <div style={{ fontSize: 36, opacity: 0.3 }}>▶</div>
          <div style={{ fontSize: 13 }}>Video will appear here</div>
        </div>
      </div>
    )
  }

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="video-wrap">
        <video
          ref={videoRef}
          src={videoSrc}
          controls
          onTimeUpdate={handleTimeUpdate}
          style={{ width: '100%', height: '100%', display: 'block', borderRadius: 'var(--radius-lg)' }}
        />
        <div className="video-overlay" />
        {job?.meta?.title && (
          <div className="video-info">
            <div style={{ fontSize: 12, fontWeight: 600, color: '#fff', textShadow: '0 1px 4px rgba(0,0,0,0.8)', maxWidth: '70%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {job.meta.title}
            </div>
            {job.meta?.duration_seconds && (
              <span className="ts">{fmt(job.meta.duration_seconds)}</span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

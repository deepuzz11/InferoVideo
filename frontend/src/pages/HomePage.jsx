import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { processVideo } from '../services/api'
import { useStore } from '../store'

const FEATURES = [
  { icon: '🎙', label: 'Local Whisper Transcription' },
  { icon: '📑', label: 'Auto Chapter Detection' },
  { icon: '🔍', label: 'Semantic Search' },
  { icon: '✨', label: 'Highlight Extraction' },
  { icon: '📝', label: 'AI Summarisation' },
  { icon: '🔒', label: 'Fully Private' },
]

const EXAMPLES = [
  'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
  'https://youtu.be/jNQXAC9IVRw',
  'https://www.youtube.com/watch?v=aircAruvnKk',
]

export default function HomePage() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const addToast = useStore(s => s.addToast)
  const navigate = useNavigate()

  const submit = async () => {
    const trimmed = url.trim()
    if (!trimmed) return
    if (!trimmed.startsWith('http')) {
      addToast('Please enter a valid URL starting with https://', 'error')
      return
    }
    setLoading(true)
    try {
      const { data } = await processVideo(trimmed)
      addToast('Pipeline started!', 'success')
      navigate(`/workspace/${data.job_id}`)
    } catch (e) {
      const msg = e.response?.data?.detail || 'Failed to start pipeline'
      addToast(msg, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleKey = e => { if (e.key === 'Enter') submit() }

  return (
    <div>
      {/* Hero */}
      <div className="hero">
        <div className="hero-eyebrow fade-in stagger-1">LOCAL-FIRST VIDEO INTELLIGENCE</div>
        <h1 className="hero-title fade-in stagger-2">
          Understand any video<br />
          <em>in minutes, not hours.</em>
        </h1>
        <p className="hero-sub fade-in stagger-3">
          Paste a YouTube URL. InferaVideo transcribes, segments,
          searches, and summarises — entirely on your machine.
          No cloud. No API keys. No data leaves your device.
        </p>

        {/* URL Form */}
        <div className="url-form fade-in stagger-4">
          <div className="url-input-wrap">
            <span className="url-icon">
              <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
            </span>
            <input
              className="url-input"
              value={url}
              onChange={e => setUrl(e.target.value)}
              onKeyDown={handleKey}
              placeholder="https://www.youtube.com/watch?v=…"
              disabled={loading}
              autoFocus
            />
          </div>
          <button
            className="btn btn-primary"
            onClick={submit}
            disabled={loading || !url.trim()}
            style={{ padding: '14px 24px', fontSize: 14 }}
          >
            {loading
              ? <><span className="spinner" /> Processing…</>
              : <>Analyse Video ↗</>
            }
          </button>
        </div>

        {/* Example URLs */}
        <div style={{ marginTop: 14, display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <span className="label">Try:</span>
          {EXAMPLES.map((ex, i) => (
            <button
              key={i}
              className="tag"
              style={{ cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 10 }}
              onClick={() => setUrl(ex)}
            >
              Example {i + 1}
            </button>
          ))}
        </div>

        {/* Feature chips */}
        <div className="features">
          {FEATURES.map((f, i) => (
            <div
              key={i}
              className="feature-chip fade-in"
              style={{ animationDelay: `${0.2 + i * 0.05}s`, opacity: 0 }}
            >
              <span>{f.icon}</span>
              <span>{f.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Divider */}
      <div className="divider" />

      {/* How it works */}
      <div style={{ padding: '32px 0' }}>
        <div className="label" style={{ marginBottom: 24, textAlign: 'center' }}>HOW IT WORKS</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
          {[
            { n: '01', title: 'Ingest', desc: 'yt-dlp downloads the video to your local machine', color: 'var(--accent)' },
            { n: '02', title: 'Transcribe', desc: 'OpenAI Whisper runs locally to produce timestamped text', color: 'var(--accent-2)' },
            { n: '03', title: 'Segment', desc: 'TF-IDF boundary detection splits content into chapters', color: 'var(--accent)' },
            { n: '04', title: 'Highlight', desc: 'Composite scoring + ffmpeg cuts the best moments', color: 'var(--accent-2)' },
            { n: '05', title: 'Summarise', desc: 'Extractive NLP condenses each chapter and the full video', color: 'var(--accent)' },
          ].map(s => (
            <div key={s.n} className="card">
              <div className="card-inner">
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: s.color, marginBottom: 6 }}>{s.n}</div>
                <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 4 }}>{s.title}</div>
                <div style={{ fontSize: 11, color: 'var(--text-3)', lineHeight: 1.5 }}>{s.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

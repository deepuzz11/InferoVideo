import React, { useEffect, useState } from 'react'
import { listJobs } from '../services/api'
import { useNavigate } from 'react-router-dom'

function timeAgo(iso) {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000
  if (diff < 60) return `${Math.floor(diff)}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

export default function JobsPage() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    listJobs(50)
      .then(r => setJobs(r.data.jobs || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div style={{ padding: '24px 0' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <div className="hero-eyebrow">HISTORY</div>
          <h2 style={{ fontSize: 28, fontWeight: 800, letterSpacing: '-0.03em' }}>Recent Jobs</h2>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/')}>
          + New Video
        </button>
      </div>

      {loading && (
        <div className="empty">
          <div className="spinner spinner-lg" style={{ margin: '0 auto 12px' }} />
          <div>Loading jobs…</div>
        </div>
      )}

      {!loading && jobs.length === 0 && (
        <div className="empty">
          <div className="empty-icon">📭</div>
          <div>No jobs yet. Process a video to get started.</div>
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => navigate('/')}>
            Process a Video
          </button>
        </div>
      )}

      <div className="jobs-list">
        {jobs.map(job => (
          <div
            key={job.job_id}
            className="job-row"
            onClick={() => navigate(`/workspace/${job.job_id}`)}
          >
            <div className={`job-dot ${job.overall_status}`} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="job-title">{job.meta?.title || job.job_id}</div>
              <div className="job-id-label">{job.job_id.slice(0, 16)}…</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
              <span className={`tag ${job.overall_status === 'complete' ? 'teal' : job.overall_status === 'failed' ? 'red' : 'accent'}`}>
                {job.overall_status}
              </span>
              <span className="job-time">{timeAgo(job.created_at)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

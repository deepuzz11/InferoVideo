import React, { useState, useEffect } from 'react'
import { healthCheck } from '../services/api'

export default function Nav() {
  const [healthy, setHealthy] = useState(null)

  useEffect(() => {
    healthCheck().then(() => setHealthy(true)).catch(() => setHealthy(false))
  }, [])

  return (
    <nav className="nav">
      <a className="nav-brand" href="/">
        <div className="nav-logo">⬡</div>
        <div>
          <div className="nav-title">Infera<span>Video</span></div>
          <div className="nav-subtitle">LOCAL · PRIVATE · INTELLIGENT</div>
        </div>
      </a>
      <div className="nav-actions">
        <span className={`badge ${healthy ? 'green' : ''}`}>
          {healthy == null ? '···' : healthy ? '● API ONLINE' : '● API OFFLINE'}
        </span>
        <a href="/docs" target="_blank" rel="noreferrer">
          <button className="btn btn-ghost btn-sm">API Docs ↗</button>
        </a>
      </div>
    </nav>
  )
}

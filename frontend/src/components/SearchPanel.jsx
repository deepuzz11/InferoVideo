import React, { useState } from 'react'
import { useStore } from '../store'
import { searchJob } from '../services/api'
import { useFormatTime } from '../hooks/useJobPoller'
import Loader from './Loader'

export default function SearchPanel({ onSeek }) {
  const job = useStore(s => s.job)
  const results = useStore(s => s.searchResults)
  const setResults = useStore(s => s.setSearchResults)
  const isSearching = useStore(s => s.isSearching)
  const setIsSearching = useStore(s => s.setIsSearching)
  const addToast = useStore(s => s.addToast)
  const fmt = useFormatTime

  const [query, setQuery] = useState('')
  const [backend, setBackend] = useState('tfidf')
  const [topK, setTopK] = useState(5)

  const canSearch = job?.transcribe_status === 'done'

  const doSearch = async () => {
    if (!query.trim() || !canSearch) return
    setIsSearching(true)
    setResults([])
    try {
      const { data } = await searchJob(job.job_id, query.trim(), topK, backend)
      setResults(data.results)
      if (!data.results.length) addToast('No matches found for that query', 'info')
    } catch {
      addToast('Search failed. Is the transcript ready?', 'error')
    } finally {
      setIsSearching(false)
    }
  }

  const handleKey = e => { if (e.key === 'Enter') doSearch() }

  return (
    <div>
      {/* Search bar */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
        <div className="input-wrap" style={{ flex: 1 }}>
          <span className="input-icon">
            <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
            </svg>
          </span>
          <input
            className="input has-icon"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKey}
            placeholder={canSearch ? 'Search inside video…' : 'Waiting for transcript…'}
            disabled={!canSearch}
          />
        </div>
        <button
          className="btn btn-primary"
          onClick={doSearch}
          disabled={!canSearch || !query.trim() || isSearching}
        >
          {isSearching
            ? <><Loader stage="search" status="running" /> Searching…</>
            : 'Search'
          }
        </button>
      </div>

      {/* Options row */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 14, alignItems: 'center' }}>
        <span className="label">Backend:</span>
        {['tfidf', 'embeddings'].map(b => (
          <button
            key={b}
            className={`tag${backend === b ? ' accent' : ''}`}
            style={{ cursor: 'pointer', border: '1px solid', transition: 'all 0.15s' }}
            onClick={() => setBackend(b)}
          >
            {b}
          </button>
        ))}
        <span className="label" style={{ marginLeft: 'auto' }}>Top:</span>
        {[3, 5, 10].map(k => (
          <button
            key={k}
            className={`tag${topK === k ? ' teal' : ''}`}
            style={{ cursor: 'pointer', border: '1px solid', transition: 'all 0.15s' }}
            onClick={() => setTopK(k)}
          >
            {k}
          </button>
        ))}
      </div>

      {/* Results */}
      {isSearching && (
        <div className="empty">
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 12 }}>
            <Loader stage="search" status="running" />
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-2)' }}>Searching transcript…</div>
        </div>
      )}

      {!isSearching && results.length === 0 && query && (
        <div className="empty">
          <div className="empty-icon">🔍</div>
          <div>No results found</div>
        </div>
      )}

      {!isSearching && results.length === 0 && !query && (
        <div className="empty">
          <div className="empty-icon">⌕</div>
          <div>Type a query to search inside the video</div>
          <div style={{ marginTop: 6, fontSize: 11, color: 'var(--text-3)' }}>
            e.g. "what is machine learning" or "key findings"
          </div>
        </div>
      )}

      {results.map((r, i) => (
        <div
          key={i}
          className="result-item fade-in"
          style={{ animationDelay: `${i * 0.04}s`, opacity: 0 }}
          onClick={() => onSeek?.(r.start)}
        >
          <div className="result-text">"{r.text}"</div>
          <div className="result-meta">
            <span className="ts">{fmt(r.start)}</span>
            <span className="ts" style={{ color: 'var(--text-3)' }}>→ {fmt(r.end)}</span>
            <div className="score-bar" style={{ flex: 1 }}>
              <div className="score-track">
                <div className="score-fill" style={{ width: `${r.score * 100}%` }} />
              </div>
              <span className="score-val">{(r.score * 100).toFixed(0)}%</span>
            </div>
            <span className={`tag ${r.backend === 'embeddings' ? 'teal' : ''}`}>{r.backend}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

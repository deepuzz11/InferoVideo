import React from 'react'

/**
 * A premium, dynamic loader that changes based on the pipeline stage.
 * Stages: ingest, transcribe, segment, highlight, summarise
 */
export default function Loader({ stage, status }) {
  if (status !== 'running') return null

  // different visuals for different stages
  const renderVisual = () => {
    switch (stage) {
      case 'ingest':
        return (
          <div className="loader-visual loader-ingest">
            <div className="scanner"></div>
          </div>
        )
      case 'transcribe':
        return (
          <div className="loader-visual loader-transcribe">
            <div className="wave-bars">
              {[1, 2, 3, 4, 5].map(i => <div key={i} className="bar" />)}
            </div>
          </div>
        )
      case 'segment':
        return (
          <div className="loader-visual loader-segment">
            <div className="orbital-dots">
              <div className="dot"></div>
              <div className="dot"></div>
              <div className="dot"></div>
            </div>
          </div>
        )
      case 'highlight':
        return (
          <div className="loader-visual loader-highlight">
            <div className="pulse-circle"></div>
            <div className="pulse-circle"></div>
          </div>
        )
      case 'summarise':
        return (
          <div className="loader-visual loader-summarise">
            <div className="typing-dots">
              <span></span><span></span><span></span>
            </div>
          </div>
        )
      case 'search':
        return (
          <div className="loader-visual loader-search">
            <div className="magnifier"></div>
          </div>
        )
      case 'insights':
        return (
          <div className="loader-visual loader-insights">
            <div className="bulb"></div>
          </div>
        )
      default:
        return <div className="spinner"></div>
    }
  }

  return (
    <div className={`dynamic-loader stage-${stage}`}>
      {renderVisual()}
    </div>
  )
}

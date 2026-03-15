import React from 'react'
import { useStore } from '../store'

export default function Toasts() {
  const toasts = useStore(s => s.toasts)
  return (
    <div className="toast-wrap">
      {toasts.map(t => (
        <div key={t.id} className={`toast ${t.type}`}>
          {t.type === 'error' && '✗ '}
          {t.type === 'success' && '✓ '}
          {t.msg}
        </div>
      ))}
    </div>
  )
}

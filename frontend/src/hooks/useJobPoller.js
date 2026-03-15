import { useEffect, useRef, useCallback } from 'react'
import { getJob } from '../services/api'
import { useStore } from '../store'

export function useJobPoller(jobId, interval = 2500) {
  const timerRef = useRef(null)
  const setJob = useStore(s => s.setJob)
  const addToast = useStore(s => s.addToast)

  const poll = useCallback(async () => {
    if (!jobId) return
    try {
      const { data } = await getJob(jobId)
      setJob(data)
      if (data.overall_status === 'complete' || data.overall_status === 'failed') {
        clearInterval(timerRef.current)
        if (data.overall_status === 'failed') {
          addToast(`Pipeline failed: ${data.error || 'unknown error'}`, 'error')
        }
      }
    } catch (e) {
      clearInterval(timerRef.current)
    }
  }, [jobId, setJob, addToast])

  useEffect(() => {
    if (!jobId) return
    poll()
    timerRef.current = setInterval(poll, interval)
    return () => clearInterval(timerRef.current)
  }, [jobId, interval, poll])
}

export function useFormatTime(seconds) {
  if (seconds == null) return '--:--'
  const t = Math.floor(seconds)
  const h = Math.floor(t / 3600)
  const m = Math.floor((t % 3600) / 60)
  const s = t % 60
  if (h) return `${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
  return `${m}:${String(s).padStart(2,'0')}`
}

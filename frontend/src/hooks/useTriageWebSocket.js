import { useEffect, useRef, useCallback } from 'react'
import { useAuthStore } from '../store/authStore'

const WS_BASE = import.meta.env.VITE_WS_URL || `ws://${window.location.host}/ws`

/**
 * useTriageWebSocket(jobId, onMessage)
 *
 * Connects to ws/triage/<jobId>?token=<jwt> and calls onMessage with
 * each received JSON object.  Automatically reconnects on unexpected close.
 */
export function useTriageWebSocket(jobId, onMessage) {
  const token = useAuthStore((s) => s.token)
  const wsRef = useRef(null)
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  const connect = useCallback(() => {
    if (!jobId || !token) return
    const url = `${WS_BASE}/triage/${jobId}?token=${token}`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data)
        onMessageRef.current(data)
      } catch (_) {}
    }

    ws.onclose = (evt) => {
      // Reconnect unless intentional (code 1000) or auth failure (4001)
      if (evt.code !== 1000 && evt.code !== 4001) {
        setTimeout(connect, 3000)
      }
    }
  }, [jobId, token])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close(1000)
    }
  }, [connect])
}

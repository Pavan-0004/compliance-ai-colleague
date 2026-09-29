import { useEffect, useRef, useState } from 'react'

const WS_URL = import.meta.env.VITE_BACKEND_WS_URL || 'ws://127.0.0.1:8000/ws'
const API_URL = import.meta.env.VITE_BACKEND_API_URL || 'http://127.0.0.1:8000'

export function useAppState() {
  const [state, setState] = useState(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)

  useEffect(() => {
    let cancelled = false
    let retryTimer = null

    function connect() {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        if (!cancelled) setConnected(true)
      }
      ws.onmessage = (event) => {
        if (cancelled) return
        setState(JSON.parse(event.data))
      }
      ws.onclose = () => {
        if (cancelled) return
        setConnected(false)
        retryTimer = setTimeout(connect, 2000)
      }
      ws.onerror = () => ws.close()
    }

    connect()
    return () => {
      cancelled = true
      clearTimeout(retryTimer)
      wsRef.current?.close()
    }
  }, [])

  const toggleMute = async () => {
    await fetch(`${API_URL}/api/mute`, { method: 'POST' })
  }

  return { state, connected, toggleMute }
}

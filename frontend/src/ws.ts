import { useEffect, useRef, useState } from "react"
import type { User } from "./discord"

export type GameKind = "connections" | "wordle"

function wsUrl(game: GameKind, date: string): string {
  const proto = location.protocol === "https:" ? "wss" : "ws"
  const isDiscord = location.hostname.endsWith("discordsays.com")
  const prefix = isDiscord ? "/.proxy/ws" : "/ws"
  return `${proto}://${location.host}${prefix}/${game}/${date}`
}

export function useGameRoom<P extends Record<string, unknown>>(
  game: GameKind,
  date: string | null,
  user: User | null,
  payload: P | null,
): Record<string, any> {
  const [players, setPlayers] = useState<Record<string, any>>({})
  const wsRef = useRef<WebSocket | null>(null)
  const payloadRef = useRef<P | null>(payload)
  const userRef = useRef<User | null>(user)

  useEffect(() => {
    if (!date) return
    setPlayers({})

    let closed = false
    let retry = 500
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined

    function connect() {
      const ws = new WebSocket(wsUrl(game, date!))
      wsRef.current = ws
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data)
        if (msg.type === "state") setPlayers(msg.players)
      }
      ws.onopen = () => {
        retry = 500
        sendUpdate()
      }
      ws.onclose = () => {
        // Ignore closes from stale sockets we've already replaced.
        if (closed || wsRef.current !== ws) return
        reconnectTimer = setTimeout(connect, retry)
        retry = Math.min(retry * 2, 10000)
      }
    }

    // Mobile suspends the activity on background / network switch; reconnect on resume.
    function wake() {
      const ws = wsRef.current
      if (closed || document.visibilityState !== "visible") return
      if (!ws || ws.readyState > WebSocket.OPEN) {
        clearTimeout(reconnectTimer)
        connect()
      }
    }

    connect()
    document.addEventListener("visibilitychange", wake)
    window.addEventListener("online", wake)

    return () => {
      closed = true
      clearTimeout(reconnectTimer)
      document.removeEventListener("visibilitychange", wake)
      window.removeEventListener("online", wake)
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [game, date])

  useEffect(() => {
    payloadRef.current = payload
    userRef.current = user
    sendUpdate()
  }, [payload, user])

  function sendUpdate() {
    const ws = wsRef.current
    const p = payloadRef.current
    const u = userRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN || !p || !u) return
    ws.send(JSON.stringify({ type: "update", user: u, ...p }))
  }

  return players
}

import type { ClientMsg, ServerMsg } from './types'

type Handler = (msg: ServerMsg) => void

let socket: WebSocket | null = null
const handlers: Handler[] = []

function getWsBaseUrl() {
  const configuredBaseUrl = import.meta.env.VITE_WS_BASE_URL
  if (configuredBaseUrl) return configuredBaseUrl.replace(/\/$/, '')

  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  const isLocalDevHost = ['localhost', '127.0.0.1', '::1'].includes(location.hostname)
  if (isLocalDevHost && location.port !== '8000') {
    return `${protocol}://${location.hostname}:8000`
  }
  return `${protocol}://${location.host}`
}

export const WS_PROTOCOL_VERSION = 'v2'
export const LEGACY_PROTOCOL_NOTE =
  '当前仍兼容旧事件名，待 conversation/coach 模块完成切换后移除。'

export const ws = {
  connect(sessionId: string, token?: string | null): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!token) {
        reject(new Error('Authentication token is missing.'))
        return
      }
      const wsBase = getWsBaseUrl()
      const params = new URLSearchParams({ token })
      socket = new WebSocket(`${wsBase}/ws/session/${sessionId}?${params.toString()}`)
      socket.onopen = () => resolve()
      socket.onerror = (event) => reject(event)
      socket.onmessage = (event) => {
        try {
          const msg: ServerMsg = JSON.parse(event.data as string)
          handlers.forEach((handler) => handler(msg))
        } catch {
          // ignore malformed messages in scaffold
        }
      }
    })
  },

  disconnect(): void {
    socket?.close()
    socket = null
  },

  send(msg: ClientMsg): void {
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(msg))
    }
  },

  onMessage(handler: Handler): () => void {
    handlers.push(handler)
    return () => {
      const index = handlers.indexOf(handler)
      if (index >= 0) handlers.splice(index, 1)
    }
  },

  isConnected(): boolean {
    return socket?.readyState === WebSocket.OPEN
  },
}


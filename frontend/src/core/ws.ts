import type { ClientMsg, ServerMsg } from './types'

type Handler = (msg: ServerMsg) => void

let socket: WebSocket | null = null
const handlers: Handler[] = []

export const ws = {
  connect(sessionId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsBase = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}`
      socket = new WebSocket(`${wsBase}/ws/session/${sessionId}`)
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
}


from __future__ import annotations

from fastapi import WebSocket

_connections: dict[str, WebSocket] = {}


def register(session_id: str, ws: WebSocket) -> None:
    _connections[session_id] = ws


def unregister(session_id: str) -> None:
    _connections.pop(session_id, None)


async def send(session_id: str, message: dict) -> None:
    ws = _connections.get(session_id)
    if ws is None:
        return
    try:
        await ws.send_json(message)
    except Exception:
        unregister(session_id)


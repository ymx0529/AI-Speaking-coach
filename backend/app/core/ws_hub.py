from __future__ import annotations

import asyncio

from fastapi import WebSocket

_connections: dict[str, WebSocket] = {}
_locks: dict[str, asyncio.Lock] = {}


def register(session_id: str, ws: WebSocket) -> None:
    _connections[session_id] = ws
    _locks.setdefault(session_id, asyncio.Lock())


def unregister(session_id: str) -> None:
    _connections.pop(session_id, None)
    _locks.pop(session_id, None)


async def send(session_id: str, message: dict) -> None:
    ws = _connections.get(session_id)
    if ws is None:
        return
    lock = _locks.setdefault(session_id, asyncio.Lock())
    try:
        async with lock:
            await ws.send_json(message)
    except Exception:
        unregister(session_id)


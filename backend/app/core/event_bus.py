from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from app.core.types import SpeakerTurnEvent

_handlers: list[Callable[[SpeakerTurnEvent], Awaitable[None]]] = []


def subscribe(handler: Callable[[SpeakerTurnEvent], Awaitable[None]]) -> None:
    _handlers.append(handler)


async def publish(event: SpeakerTurnEvent) -> None:
    for handler in _handlers:
        asyncio.create_task(handler(event))


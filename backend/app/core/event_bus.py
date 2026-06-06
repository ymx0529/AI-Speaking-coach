from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

_handlers: list[Callable[[Any], Awaitable[None]]] = []


def subscribe(handler: Callable[[Any], Awaitable[None]]) -> None:
    _handlers.append(handler)


async def publish(event: Any) -> None:
    for handler in _handlers:
        asyncio.create_task(handler(event))

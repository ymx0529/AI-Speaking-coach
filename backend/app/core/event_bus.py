from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger(__name__)

# Handlers receive any published event (e.g. TurnTranscriptReadyEvent, SpeakerTurnEvent).
_handlers: list[Callable[[Any], Awaitable[None]]] = []


def subscribe(handler: Callable[[Any], Awaitable[None]]) -> None:
    _handlers.append(handler)
    logger.info("event_bus: subscribed handler %s (total=%d)", handler.__name__, len(_handlers))


async def _run_safe(handler: Callable[[Any], Awaitable[None]], event: Any) -> None:
    try:
        await handler(event)
    except Exception:
        logger.exception("event_bus: handler %s raised an exception", handler.__name__)


async def publish(event: Any) -> None:
    logger.info("event_bus: publishing %s to %d handler(s)", type(event).__name__, len(_handlers))
    for handler in _handlers:
        asyncio.create_task(_run_safe(handler, event))

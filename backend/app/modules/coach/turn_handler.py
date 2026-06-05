from __future__ import annotations

from app.core.types import SpeakerTurnEvent


async def on_turn_event(event: SpeakerTurnEvent) -> None:
    _ = event


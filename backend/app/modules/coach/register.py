from fastapi import FastAPI


def register_coach(app: FastAPI) -> None:
    from app.core import event_bus
    from app.modules.coach.router import router as coach_router
    from app.modules.coach.turn_handler import on_turn_event

    event_bus.subscribe(on_turn_event)
    app.include_router(coach_router, prefix="/api")


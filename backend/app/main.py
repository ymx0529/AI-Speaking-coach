from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(title="SpeakCoach API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _register_modules() -> None:
    from app.modules.coach.register import register_coach
    from app.modules.conversation.register import register_conversation

    register_conversation(app)
    register_coach(app)


_register_modules()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


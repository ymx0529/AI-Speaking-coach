from fastapi import FastAPI


def register_conversation(app: FastAPI) -> None:
    from app.modules.conversation.router import router as ws_router
    from app.modules.conversation.scene_router import router as scene_router

    app.include_router(ws_router)
    app.include_router(scene_router, prefix="/api")


from fastapi import FastAPI


def register_auth(app: FastAPI) -> None:
    from app.modules.auth.router import router as auth_router

    app.include_router(auth_router, prefix="/api")

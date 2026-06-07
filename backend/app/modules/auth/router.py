from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.modules.auth.dependencies import CurrentUser, extract_bearer_token, require_auth_user, security
from app.modules.auth import service

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthUser(CurrentUser):
    pass


class AuthResponse(BaseModel):
    token: str
    user: AuthUser


class AuthOkResponse(BaseModel):
    ok: bool


class RegisterRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None


class LoginRequest(BaseModel):
    email: str | None = None
    password: str | None = None


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest) -> AuthResponse:
    token, user = service.register_user(
        name=payload.name,
        email=payload.email,
        password=payload.password,
    )
    return AuthResponse(token=token, user=AuthUser(**user))


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest) -> AuthResponse:
    token, user = service.login_user(email=payload.email, password=payload.password)
    return AuthResponse(token=token, user=AuthUser(**user))


@router.get("/me", response_model=AuthUser)
async def me(user: CurrentUser = Depends(require_auth_user)) -> AuthUser:
    return AuthUser(**user.model_dump())


@router.post("/logout", response_model=AuthOkResponse)
async def logout(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> AuthOkResponse:
    token = extract_bearer_token(credentials)
    if service.get_user_by_token(token) is None:
        raise HTTPException(status_code=401, detail="Authentication token is invalid.")
    service.logout_token(token)
    return AuthOkResponse(ok=True)

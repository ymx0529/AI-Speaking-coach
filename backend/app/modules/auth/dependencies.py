from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.modules.auth import service

security = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    id: str
    name: str
    email: str
    created_at: str


def extract_bearer_token(credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authentication token is missing.")
    return credentials.credentials


def require_auth_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> CurrentUser:
    token = extract_bearer_token(credentials)
    user = service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication token is invalid.")
    return CurrentUser(**user)


def get_user_from_token(token: str | None) -> CurrentUser | None:
    user = service.get_user_by_token(token)
    if user is None:
        return None
    return CurrentUser(**user)

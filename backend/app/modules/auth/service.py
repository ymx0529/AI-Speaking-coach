from __future__ import annotations

import hashlib
import json
import re
import secrets
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

BACKEND_ROOT = Path(__file__).resolve().parents[3]
USERS_FILE = BACKEND_ROOT / "runtime" / "users.json"
SESSIONS_FILE = BACKEND_ROOT / "runtime" / "sessions.json"

_PASSWORD_ITERATIONS = 120_000
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SESSION_TTL = timedelta(days=1)
_lock = threading.Lock()
_sessions: dict[str, tuple[str, datetime]] = {}


def register_user(*, name: str | None, email: str | None, password: str | None) -> tuple[str, dict]:
    clean_name = _validate_name(name)
    clean_email = _validate_email(email)
    clean_password = _validate_password(password)

    with _lock:
        users = _read_users()
        if _find_user_by_email(users, clean_email) is not None:
            raise HTTPException(status_code=409, detail="Email is already registered.")

        salt = secrets.token_hex(16)
        user = {
            "id": str(uuid4()),
            "name": clean_name,
            "email": clean_email,
            "password_hash": _hash_password(clean_password, salt),
            "salt": salt,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        users.append(user)
        _write_users(users)

    token = _issue_token(user["id"])
    return token, _public_user(user)


def login_user(*, email: str | None, password: str | None) -> tuple[str, dict]:
    clean_email = _validate_email(email)
    if not password:
        raise HTTPException(status_code=400, detail="Password is required.")

    with _lock:
        user = _find_user_by_email(_read_users(), clean_email)

    if user is None or not _verify_password(password, user):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = _issue_token(user["id"])
    return token, _public_user(user)


def get_user_by_token(token: str | None) -> dict | None:
    if not token:
        return None

    with _lock:
        _load_sessions()
        session = _sessions.get(token)
        if session is None:
            return None

        user_id, expires_at = session
        if expires_at <= datetime.now(timezone.utc):
            _sessions.pop(token, None)
            _write_sessions(_sessions)
            return None

        for user in _read_users():
            if user.get("id") == user_id:
                return _public_user(user)
    return None


def logout_token(token: str) -> None:
    with _lock:
        _load_sessions()
        _sessions.pop(token, None)
        _write_sessions(_sessions)


def clear_sessions() -> None:
    with _lock:
        _sessions.clear()
        if SESSIONS_FILE.exists():
            SESSIONS_FILE.unlink()


def _issue_token(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    with _lock:
        _load_sessions()
        _sessions[token] = (user_id, datetime.now(timezone.utc) + SESSION_TTL)
        _write_sessions(_sessions)
    return token


def _load_sessions() -> None:
    if _sessions or not SESSIONS_FILE.exists():
        return

    try:
        with SESSIONS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return

    if not isinstance(data, dict):
        return

    now = datetime.now(timezone.utc)
    changed = False
    for token, item in data.items():
        if not isinstance(token, str) or not isinstance(item, dict):
            changed = True
            continue
        user_id = item.get("user_id")
        expires_at_raw = item.get("expires_at")
        if not isinstance(user_id, str) or not isinstance(expires_at_raw, str):
            changed = True
            continue
        try:
            expires_at = datetime.fromisoformat(expires_at_raw)
        except ValueError:
            changed = True
            continue
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            changed = True
            continue
        _sessions[token] = (user_id, expires_at)

    if changed:
        _write_sessions(_sessions)


def _write_sessions(sessions: dict[str, tuple[str, datetime]]) -> None:
    SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        token: {
            "user_id": user_id,
            "expires_at": expires_at.isoformat(),
        }
        for token, (user_id, expires_at) in sessions.items()
    }
    with SESSIONS_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def _read_users() -> list[dict]:
    if not USERS_FILE.exists():
        return []

    with USERS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise HTTPException(status_code=500, detail="User store is invalid.")
    return data


def _write_users(users: list[dict]) -> None:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with USERS_FILE.open("w", encoding="utf-8") as file:
        json.dump(users, file, ensure_ascii=False, indent=2)


def _find_user_by_email(users: list[dict], email: str) -> dict | None:
    for user in users:
        if str(user.get("email", "")).lower() == email:
            return user
    return None


def _validate_name(name: str | None) -> str:
    clean_name = (name or "").strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Name is required.")
    if len(clean_name) > 80:
        raise HTTPException(status_code=400, detail="Name is too long.")
    return clean_name


def _validate_email(email: str | None) -> str:
    clean_email = (email or "").strip().lower()
    if not clean_email:
        raise HTTPException(status_code=400, detail="Email is required.")
    if not _EMAIL_RE.match(clean_email):
        raise HTTPException(status_code=400, detail="Email format is invalid.")
    return clean_email


def _validate_password(password: str | None) -> str:
    if not password:
        raise HTTPException(status_code=400, detail="Password is required.")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    return password


def _hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        _PASSWORD_ITERATIONS,
    )
    return digest.hex()


def _verify_password(password: str, user: dict) -> bool:
    salt = str(user.get("salt", ""))
    expected_hash = str(user.get("password_hash", ""))
    if not salt or not expected_hash:
        return False
    actual_hash = _hash_password(password, salt)
    return secrets.compare_digest(actual_hash, expected_hash)


def _public_user(user: dict) -> dict:
    return {
        "id": str(user["id"]),
        "name": str(user["name"]),
        "email": str(user["email"]),
        "created_at": str(user["created_at"]),
    }

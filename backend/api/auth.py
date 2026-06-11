import hashlib
import json
import os
import secrets
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["auth"])

# In-memory session store — dev only, resets on restart.
_sessions: dict[str, str] = {}  # token -> account_id


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


def _account_path() -> str:
    return os.environ.get("DOBRYBOT_ACCOUNT_PATH", "data/account.json")


def _hash_pw(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 260_000
    ).hex()


def _load_account() -> Optional[dict]:
    p = Path(_account_path())
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _save_account(account: dict) -> None:
    p = Path(_account_path())
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(account, f, indent=2)


def _token_from_header(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(None, 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


@router.post("/auth/register")
async def register(req: RegisterRequest):
    if _load_account():
        raise HTTPException(
            status_code=409,
            detail="An account already exists. This dev build supports one account.",
        )
    salt = secrets.token_hex(16)
    _save_account(
        {
            "id": "default",
            "email": req.email,
            "full_name": req.full_name,
            "salt": salt,
            "password_hash": _hash_pw(req.password, salt),
        }
    )
    return {"registered": True, "email": req.email}


@router.post("/auth/login")
async def login(req: LoginRequest):
    account = _load_account()
    if not account or account["email"] != req.email:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    if not secrets.compare_digest(
        _hash_pw(req.password, account["salt"]), account["password_hash"]
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    token = secrets.token_hex(32)
    _sessions[token] = account["id"]
    return {"token": token, "email": account["email"]}


@router.get("/auth/me")
async def me(authorization: Optional[str] = Header(default=None)):
    token = _token_from_header(authorization)
    if not token or token not in _sessions:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    account = _load_account()
    if not account:
        raise HTTPException(status_code=401, detail="Account not found.")
    return {
        "id": account["id"],
        "email": account["email"],
        "full_name": account.get("full_name", ""),
    }


@router.post("/auth/logout")
async def logout(authorization: Optional[str] = Header(default=None)):
    token = _token_from_header(authorization)
    if token and token in _sessions:
        del _sessions[token]
    return {"logged_out": True}

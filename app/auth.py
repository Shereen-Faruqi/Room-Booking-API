"""Fake login: the X-User-Token header is mapped to a demo user from config/demo_users.json."""
import json
from pathlib import Path

from fastapi import Header, HTTPException

USERS_FILE = Path(__file__).resolve().parent.parent / "config" / "demo_users.json"


def _load_tokens() -> dict[str, str]:
    data = json.loads(USERS_FILE.read_text())
    return {user["token"]: user["username"] for user in data["users"]}


TOKENS = _load_tokens()


def current_user(x_user_token: str | None = Header(default=None)) -> str:
    """Return the username for the request's token, or answer 401."""
    username = TOKENS.get(x_user_token or "")
    if username is None:
        raise HTTPException(status_code=401, detail="Missing or invalid X-User-Token header")
    return username

"""Аккаунты на сайте: почта с паролем и вход через Telegram.

Пароли — pbkdf2 через Werkzeug, сессия — подписанная cookie Flask.
Telegram Login Widget проверяется по HMAC с секретом из токена бота.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import time
from typing import Any

from flask import session
from werkzeug.security import check_password_hash, generate_password_hash

import config
import db

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
PASSWORD_MIN = 8


def hash_password(password: str) -> str:
    return generate_password_hash(password, method="pbkdf2:sha256:260000")


def verify_password(password_hash: str | None, password: str) -> bool:
    if not password_hash:
        return False
    try:
        return check_password_hash(password_hash, password)
    except (ValueError, TypeError):
        return False


def valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email or "")) and len(email) <= 254


def start_session(user_id: int) -> None:
    session.clear()
    session["uid"] = int(user_id)
    session.permanent = True


def end_session() -> None:
    session.clear()


def current_user() -> dict[str, Any] | None:
    user_id = session.get("uid")
    if not isinstance(user_id, int):
        return None
    return db.get_user(user_id)


def user_payload(user: dict[str, Any] | None) -> dict[str, Any] | None:
    if not user:
        return None
    return {
        "id": user["id"],
        "email": user["email"],
        "telegram_id": user["telegram_id"],
        "telegram_username": user["telegram_username"],
        "name": user["telegram_name"]
        or (user["email"].split("@")[0] if user["email"] else "Пользователь"),
        "photo": user["telegram_photo"],
    }


def telegram_login_ready() -> bool:
    return bool(config.BOT_TOKEN and config.BOT_USERNAME)


def verify_telegram(data: dict[str, Any]) -> bool:
    """Проверка подписи Telegram Login Widget."""
    if not config.BOT_TOKEN:
        return False

    received = str(data.get("hash") or "")
    if not received:
        return False

    items = {key: value for key, value in data.items() if key != "hash" and value is not None}
    check_string = "\n".join(f"{key}={items[key]}" for key in sorted(items))
    secret = hashlib.sha256(config.BOT_TOKEN.encode("utf-8")).digest()
    expected = hmac.new(secret, check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        return False

    try:
        auth_date = int(items.get("auth_date", "0"))
    except (TypeError, ValueError):
        return False
    return 0 < time.time() - auth_date < 86400


def telegram_payload(data: dict[str, Any]) -> dict[str, Any]:
    try:
        telegram_id = int(data.get("id"))
    except (TypeError, ValueError):
        raise ValueError("bad_telegram_id")

    return {
        "telegram_id": telegram_id,
        "telegram_username": str(data.get("username") or "")[:64] or None,
        "telegram_name": " ".join(
            part for part in (data.get("first_name"), data.get("last_name")) if part
        )[:128] or None,
        "telegram_photo": str(data.get("photo_url") or "")[:512] or None,
    }

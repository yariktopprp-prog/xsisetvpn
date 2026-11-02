"""Настройки xsiset vpn: тарифы, бот, панель 3x-ui, платёжные провайдеры.

Значения читаются из окружения, при наличии — из server/.env.
Формат .env простой: KEY=VALUE, решётки — комментарии.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SERVER_DIR = BASE_DIR / "server"


def _load_dotenv(path: Path) -> None:
    """Подхватить server/.env, не перетирая уже заданные переменные."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _int(name: str, default: int) -> int:
    try:
        return int(_env(name, str(default)))
    except ValueError:
        return default


_load_dotenv(SERVER_DIR / ".env")

DATA_DIR = Path(_env("XSISET_DATA_DIR", str(SERVER_DIR / "data"))).resolve()
DB_PATH = Path(_env("XSISET_DB", str(DATA_DIR / "orders.sqlite3"))).resolve()


def _session_secret() -> str:
    value = _env("XSISET_SECRET_KEY")
    if value:
        return value
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    key_file = DATA_DIR / "session.key"
    if key_file.is_file():
        stored = key_file.read_text(encoding="utf-8").strip()
        if stored:
            return stored
    generated = secrets.token_hex(32)
    key_file.write_text(generated, encoding="utf-8")
    return generated


# --- сайт и сессии -------------------------------------------------------

SECRET_KEY = _session_secret()
COOKIE_SECURE = _flag("XSISET_COOKIE_SECURE", False)
HOST = _env("XSISET_HOST", "127.0.0.1")
PORT = _int("XSISET_PORT", 8124)
DEMO = _flag("XSISET_DEMO")
CONTACT_EMAIL = _env("XSISET_CONTACT_EMAIL", "xsiset@proton.me")

# --- Telegram ------------------------------------------------------------

BOT_USERNAME = _env("XSISET_BOT", "xsisetvpnbot").lstrip("@")
BOT_TOKEN = _env("XSISET_BOT_TOKEN")

# --- тарифы --------------------------------------------------------------

CURRENCY = "RUB"
PLANS = (
    {"id": "m1", "months": 1, "days": 30, "price": 100},
    {"id": "m3", "months": 3, "days": 90, "price": 270},
    {"id": "m6", "months": 6, "days": 180, "price": 500},
    {"id": "m12", "months": 12, "days": 365, "price": 900},
)
PLANS_BY_ID = {plan["id"]: plan for plan in PLANS}

ORDER_TTL_HOURS = _int("XSISET_ORDER_TTL_HOURS", 24)
PAYMENT_TTL_MINUTES = _int("XSISET_PAYMENT_TTL_MINUTES", 60)
CONSENT_VERSION = _env("XSISET_CONSENT_VERSION", "2026-11-01")
RECONCILE_SECONDS = _int("XSISET_RECONCILE_SECONDS", 120)

# --- платежи -------------------------------------------------------------

CRYPTOPAY_TOKEN = _env("XSISET_CRYPTOPAY_TOKEN")
CRYPTOPAY_API = _env("XSISET_CRYPTOPAY_API", "https://pay.crypt.bot/api").rstrip("/")
CRYPTO_ASSETS = tuple(
    item.strip().upper()
    for item in _env("XSISET_CRYPTO_ASSETS", "USDT,TRX,TON").split(",")
    if item.strip()
)

PLATEGA_MERCHANT_ID = _env("XSISET_PLATEGA_MERCHANT_ID")
PLATEGA_SECRET = _env("XSISET_PLATEGA_SECRET")
PLATEGA_API = _env("XSISET_PLATEGA_API", "https://app.platega.io").rstrip("/")
PLATEGA_METHODS = _int("XSISET_PLATEGA_METHOD", 0)

# --- панель 3x-ui --------------------------------------------------------

PANEL_URL = _env("XSISET_PANEL_URL").rstrip("/")
PANEL_TOKEN = _env("XSISET_PANEL_TOKEN")
PANEL_INBOUND_IDS = tuple(
    int(item)
    for item in _env("XSISET_PANEL_INBOUNDS", "5,11,13,16,17").split(",")
    if item.strip().isdigit()
)
PANEL_SUB_BASE = _env("XSISET_PANEL_SUB_BASE").rstrip("/")
PANEL_VERIFY_TLS = _flag("XSISET_PANEL_VERIFY_TLS", True)
PANEL_TIMEOUT = _int("XSISET_PANEL_TIMEOUT", 20)
PANEL_MODE = _env("XSISET_PANEL_MODE") or ("live" if PANEL_URL and PANEL_TOKEN else "dry")

# --- признаки готовности -------------------------------------------------

CRYPTOPAY_READY = bool(CRYPTOPAY_TOKEN)
PLATEGA_READY = bool(PLATEGA_MERCHANT_ID and PLATEGA_SECRET)
TELEGRAM_LOGIN_READY = bool(BOT_TOKEN)
PANEL_LIVE = PANEL_MODE == "live" and bool(PANEL_URL and PANEL_TOKEN)

"""SQLite: пользователи, заказы, события.

Деньги хранятся в копейках. Все времена — ISO 8601 в UTC.
"""

from __future__ import annotations

import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator

from config import CONSENT_VERSION, CURRENCY, DB_PATH, ORDER_TTL_HOURS, PLANS_BY_ID

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    email              TEXT UNIQUE,
    password_hash      TEXT,
    telegram_id        INTEGER UNIQUE,
    telegram_username  TEXT,
    telegram_name      TEXT,
    telegram_photo     TEXT,
    created_at         TEXT NOT NULL,
    last_login_at      TEXT,
    consent_at         TEXT,
    consent_ip         TEXT,
    consent_version    TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    id                 TEXT PRIMARY KEY,
    access_token       TEXT NOT NULL,
    user_id            INTEGER,
    buyer_type         TEXT NOT NULL,
    email              TEXT,
    plan_id            TEXT NOT NULL,
    months             INTEGER NOT NULL,
    amount             INTEGER NOT NULL,
    currency           TEXT NOT NULL,
    status             TEXT NOT NULL,
    method             TEXT,
    asset              TEXT,
    provider_id        TEXT,
    pay_url            TEXT,
    payment_expires_at TEXT,
    checked_at         TEXT,
    paid_at            TEXT,
    key_email          TEXT,
    key_uuid           TEXT,
    key_sub_id         TEXT,
    key_sub_url        TEXT,
    key_issued_at      TEXT,
    key_valid_until    TEXT,
    key_error          TEXT,
    consent_at         TEXT,
    consent_ip         TEXT,
    consent_version    TEXT,
    created_at         TEXT NOT NULL,
    updated_at         TEXT NOT NULL,
    expires_at         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   TEXT NOT NULL,
    type       TEXT NOT NULL,
    payload    TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

# Индексы создаются после миграций: старые базы не знают новых колонок.
INDEXES = """
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_provider ON orders(provider_id);
CREATE INDEX IF NOT EXISTS idx_events_order ON events(order_id);
"""

# колонки, добавленные после первой версии: мягкая миграция старых баз
MIGRATIONS = {
    "orders": {
        "access_token": "TEXT NOT NULL DEFAULT ''",
        "user_id": "INTEGER",
        "buyer_type": "TEXT",
        "email": "TEXT",
        "months": "INTEGER NOT NULL DEFAULT 1",
        "method": "TEXT",
        "asset": "TEXT",
        "provider_id": "TEXT",
        "pay_url": "TEXT",
        "payment_expires_at": "TEXT",
        "checked_at": "TEXT",
        "key_email": "TEXT",
        "key_uuid": "TEXT",
        "key_sub_id": "TEXT",
        "key_sub_url": "TEXT",
        "key_issued_at": "TEXT",
        "key_valid_until": "TEXT",
        "key_error": "TEXT",
        "consent_at": "TEXT",
        "consent_ip": "TEXT",
        "consent_version": "TEXT",
        "updated_at": "TEXT NOT NULL DEFAULT ''",
    },
    "users": {
        "email": "TEXT",
        "password_hash": "TEXT",
        "telegram_id": "INTEGER",
        "telegram_username": "TEXT",
        "telegram_name": "TEXT",
        "telegram_photo": "TEXT",
        "last_login_at": "TEXT",
        "consent_at": "TEXT",
        "consent_ip": "TEXT",
        "consent_version": "TEXT",
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def now_dt() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def session() -> Iterator[sqlite3.Connection]:
    """Соединение на операцию: commit при успехе, close в любом случае."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    for name, ddl in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def init_db() -> None:
    with session() as conn:
        conn.executescript(SCHEMA)
        for table, columns in MIGRATIONS.items():
            _ensure_columns(conn, table, columns)
        conn.executescript(INDEXES)


def new_order_id() -> str:
    return "xs" + secrets.token_urlsafe(14).replace("-", "").replace("_", "")[:16]


def new_access_token() -> str:
    return secrets.token_hex(16)


def log_event(conn: sqlite3.Connection, order_id: str, kind: str, payload: dict[str, Any]) -> None:
    conn.execute(
        "INSERT INTO events (order_id, type, payload, created_at) VALUES (?, ?, ?, ?)",
        (order_id, kind, json.dumps(payload, ensure_ascii=False), now_iso()),
    )


# -------------------------------- заказы ---------------------------------


def create_order(
    plan_id: str,
    *,
    user_id: int | None = None,
    buyer_type: str = "anon",
    email: str | None = None,
    consent_ip: str = "",
) -> dict[str, Any] | None:
    plan = PLANS_BY_ID.get(plan_id)
    if not plan:
        return None

    order_id = new_order_id()
    token = new_access_token()
    created = now_dt()
    expires = created + timedelta(hours=ORDER_TTL_HOURS)
    stamp = created.isoformat()

    with session() as conn:
        conn.execute(
            """INSERT INTO orders
               (id, access_token, user_id, buyer_type, email, plan_id, months,
                amount, currency, status, consent_at, consent_ip, consent_version,
                created_at, updated_at, expires_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?)""",
            (
                order_id,
                token,
                user_id,
                buyer_type,
                email,
                plan_id,
                plan["months"],
                plan["price"] * 100,
                CURRENCY,
                stamp,
                consent_ip,
                CONSENT_VERSION,
                stamp,
                stamp,
                expires.isoformat(),
            ),
        )
        log_event(conn, order_id, "created", {"plan_id": plan_id, "buyer": buyer_type})
        row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return dict(row) if row else None


def get_order(order_id: str) -> dict[str, Any] | None:
    with session() as conn:
        row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not row:
            return None
        row = _expire_if_needed(conn, row)
    return dict(row)


def _expire_if_needed(conn: sqlite3.Connection, row: sqlite3.Row) -> sqlite3.Row:
    if row["status"] != "pending":
        return row
    expires = parse_dt(row["expires_at"])
    if expires is None or now_dt() < expires:
        return row
    conn.execute(
        "UPDATE orders SET status = 'expired', updated_at = ? WHERE id = ? AND status = 'pending'",
        (now_iso(), row["id"]),
    )
    log_event(conn, row["id"], "expired", {})
    return conn.execute("SELECT * FROM orders WHERE id = ?", (row["id"],)).fetchone()


def set_payment(
    order_id: str,
    *,
    method: str,
    provider_id: str,
    pay_url: str,
    asset: str | None = None,
    expires_at: str | None = None,
) -> bool:
    with session() as conn:
        cur = conn.execute(
            """UPDATE orders
               SET method = ?, provider_id = ?, pay_url = ?, asset = ?,
                   payment_expires_at = ?, checked_at = ?, updated_at = ?
               WHERE id = ? AND status = 'pending'""",
            (method, provider_id, pay_url, asset, expires_at, now_iso(), now_iso(), order_id),
        )
        if cur.rowcount:
            log_event(conn, order_id, "payment_created", {"method": method, "provider_id": provider_id})
        return bool(cur.rowcount)


def mark_checked(order_id: str) -> None:
    with session() as conn:
        conn.execute("UPDATE orders SET checked_at = ? WHERE id = ?", (now_iso(), order_id))


def mark_paid(order_id: str, provider_id: str | None = None) -> bool:
    with session() as conn:
        row = conn.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not row:
            return False
        if row["status"] == "paid":
            return True
        if row["status"] == "failed":
            log_event(conn, order_id, "paid_after_close", {"status": row["status"]})
            return False
        conn.execute(
            """UPDATE orders
               SET status = 'paid', paid_at = ?, provider_id = COALESCE(?, provider_id),
                   checked_at = ?, updated_at = ?
               WHERE id = ?""",
            (now_iso(), provider_id, now_iso(), now_iso(), order_id),
        )
        log_event(conn, order_id, "paid", {"provider_id": provider_id, "was": row["status"]})
    return True


def mark_failed(order_id: str, reason: str = "") -> bool:
    with session() as conn:
        row = conn.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not row or row["status"] != "pending":
            return False
        conn.execute(
            "UPDATE orders SET status = 'failed', updated_at = ? WHERE id = ?",
            (now_iso(), order_id),
        )
        log_event(conn, order_id, "failed", {"reason": reason})
    return True


def set_key(
    order_id: str,
    *,
    key_email: str,
    key_uuid: str,
    key_sub_id: str,
    key_sub_url: str,
    valid_until: str,
) -> bool:
    with session() as conn:
        cur = conn.execute(
            """UPDATE orders
               SET key_email = ?, key_uuid = ?, key_sub_id = ?, key_sub_url = ?,
                   key_issued_at = ?, key_valid_until = ?, key_error = NULL, updated_at = ?
               WHERE id = ? AND key_issued_at IS NULL""",
            (key_email, key_uuid, key_sub_id, key_sub_url, now_iso(), valid_until, now_iso(), order_id),
        )
        if cur.rowcount:
            log_event(conn, order_id, "key_issued", {"key_email": key_email})
        return bool(cur.rowcount)


def set_key_error(order_id: str, message: str) -> None:
    with session() as conn:
        conn.execute(
            "UPDATE orders SET key_error = ?, updated_at = ? WHERE id = ?",
            (message[:400], now_iso(), order_id),
        )
        log_event(conn, order_id, "key_error", {"message": message[:400]})


def list_user_orders(user_id: int, limit: int = 50) -> list[dict[str, Any]]:
    with session() as conn:
        rows = conn.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def pending_with_payment(limit: int = 25) -> list[dict[str, Any]]:
    """Заказы, которые ещё ждут оплаты: их проверяет фоновый сверщик."""
    with session() as conn:
        rows = conn.execute(
            """SELECT * FROM orders
               WHERE status = 'pending' AND provider_id IS NOT NULL AND provider_id != ''
               ORDER BY created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


# ------------------------------ пользователи -----------------------------


def create_user(
    *,
    email: str | None = None,
    password_hash: str | None = None,
    telegram_id: int | None = None,
    telegram_username: str | None = None,
    telegram_name: str | None = None,
    telegram_photo: str | None = None,
    consent_ip: str = "",
) -> dict[str, Any]:
    stamp = now_iso()
    with session() as conn:
        cur = conn.execute(
            """INSERT INTO users
               (email, password_hash, telegram_id, telegram_username, telegram_name,
                telegram_photo, created_at, last_login_at, consent_at, consent_ip, consent_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                email.lower() if email else None,
                password_hash,
                telegram_id,
                telegram_username,
                telegram_name,
                telegram_photo,
                stamp,
                stamp,
                stamp if consent_ip else None,
                consent_ip or None,
                CONSENT_VERSION if consent_ip else None,
            ),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def get_user(user_id: int) -> dict[str, Any] | None:
    with session() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def get_user_by_email(email: str) -> dict[str, Any] | None:
    with session() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
    return dict(row) if row else None


def get_user_by_telegram(telegram_id: int) -> dict[str, Any] | None:
    with session() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
    return dict(row) if row else None


def update_user_telegram(
    user_id: int,
    *,
    username: str | None,
    name: str | None,
    photo: str | None,
) -> None:
    with session() as conn:
        conn.execute(
            """UPDATE users
               SET telegram_username = ?, telegram_name = ?, telegram_photo = ?
               WHERE id = ?""",
            (username, name, photo, user_id),
        )


def touch_login(user_id: int) -> None:
    with session() as conn:
        conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (now_iso(), user_id))


def set_user_consent(user_id: int, ip: str) -> None:
    with session() as conn:
        conn.execute(
            """UPDATE users
               SET consent_at = COALESCE(consent_at, ?), consent_ip = COALESCE(consent_ip, ?),
                   consent_version = COALESCE(consent_version, ?)
               WHERE id = ?""",
            (now_iso(), ip, CONSENT_VERSION, user_id),
        )

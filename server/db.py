"""SQLite: Zero-Knowledge временный буфер заказов.
Динамическая миграция без потери данных, безопасный TTL только для выданных ключей.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator

import secure
from config import CONSENT_VERSION, CURRENCY, DB_PATH, ORDER_TTL_HOURS, PLANS_BY_ID

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id              TEXT PRIMARY KEY,
    token_hash      TEXT NOT NULL,
    plan_id         TEXT NOT NULL,
    amount          INTEGER NOT NULL,
    currency        TEXT NOT NULL,
    status          TEXT NOT NULL,
    method          TEXT,
    provider_id     TEXT,
    pay_url         TEXT,
    key_sub_url     TEXT,
    key_valid_until TEXT,
    key_issued_at   TEXT,
    consent_at      TEXT NOT NULL,
    consent_version TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_provider ON orders(provider_id);
"""


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


def hash_token(raw_token: str) -> str:
    if not raw_token:
        return ""
    return "th_" + hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA secure_delete=ON")
    return conn


@contextmanager
def session() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _compact() -> None:
    """Перезаписывает файл БД, чтобы в WAL/свободных страницах не осталось открытых данных."""
    raw = connect()
    try:
        raw.isolation_level = None
        raw.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        raw.execute("VACUUM")
    finally:
        raw.close()


def init_db() -> None:
    """Безопасная миграция с динамическим сопоставлением имеющихся колонок."""
    changed = False
    with session() as conn:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
        if cur.fetchone():
            existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(orders)").fetchall()}
            required_cols = {"token_hash", "key_issued_at"}
            if not required_cols.issubset(existing_cols):
                conn.execute("ALTER TABLE orders RENAME TO orders_legacy")
                conn.executescript(SCHEMA)

                # Безопасно вытягиваем только те поля, которые реально существуют
                token_expr = "access_token" if "access_token" in existing_cols else ("token_hash" if "token_hash" in existing_cols else "''")
                issued_expr = "key_issued_at" if "key_issued_at" in existing_cols else ("paid_at" if "paid_at" in existing_cols else "NULL")
                consent_at_expr = "consent_at" if "consent_at" in existing_cols else "created_at"
                consent_ver_expr = "consent_version" if "consent_version" in existing_cols else f"'{CONSENT_VERSION}'"
                sub_expr = "key_sub_url" if "key_sub_url" in existing_cols else "NULL"
                valid_expr = "key_valid_until" if "key_valid_until" in existing_cols else "NULL"
                provider_expr = "provider_id" if "provider_id" in existing_cols else "NULL"
                pay_url_expr = "pay_url" if "pay_url" in existing_cols else "NULL"
                method_expr = "method" if "method" in existing_cols else "NULL"

                conn.execute(f"""
                    INSERT INTO orders (
                        id, token_hash, plan_id, amount, currency, status,
                        method, provider_id, pay_url, key_sub_url, key_valid_until, key_issued_at,
                        consent_at, consent_version, created_at
                    )
                    SELECT
                        id,
                        {token_expr},
                        plan_id,
                        amount,
                        currency,
                        status,
                        {method_expr},
                        {provider_expr},
                        {pay_url_expr},
                        {sub_expr},
                        {valid_expr},
                        {issued_expr},
                        {consent_at_expr},
                        {consent_ver_expr},
                        created_at
                    FROM orders_legacy
                """)
                conn.execute("DROP TABLE orders_legacy")
        else:
            conn.executescript(SCHEMA)

        # Шифруем всё, что успело сохраниться в открытом виде, и хэшируем старые токены.
        for row in conn.execute(
            "SELECT id, token_hash, key_sub_url, provider_id, pay_url, key_issued_at, created_at FROM orders"
        ).fetchall():
            updates: dict[str, Any] = {}
            token = row["token_hash"] or ""
            if token == "migrated":
                updates["token_hash"] = ""
            elif token and not token.startswith("th_"):
                updates["token_hash"] = hash_token(token)
            for field in ("key_sub_url", "provider_id", "pay_url"):
                value = row[field]
                if value and not secure.is_encrypted(value):
                    updates[field] = secure.protect(value, aad=row["id"])
            if row["key_sub_url"] and not row["key_issued_at"]:
                updates["key_issued_at"] = row["created_at"]
            if updates:
                assignments = ", ".join(f"{name} = ?" for name in updates)
                conn.execute(
                    f"UPDATE orders SET {assignments} WHERE id = ?",
                    (*updates.values(), row["id"]),
                )
                changed = True

        conn.execute("DROP TABLE IF EXISTS events")
        conn.execute("DROP TABLE IF EXISTS users")

    if changed:
        _compact()


def new_order_id() -> str:
    return "xs" + secrets.token_urlsafe(14).replace("-", "").replace("_", "")[:16]


def new_access_token() -> str:
    return secrets.token_hex(16)


def create_order(plan_id: str) -> tuple[dict[str, Any] | None, str]:
    plan = PLANS_BY_ID.get(plan_id)
    if not plan:
        return None, ""

    order_id = new_order_id()
    raw_token = new_access_token()
    token_hashed = hash_token(raw_token)
    created = now_iso()

    with session() as conn:
        conn.execute(
            """INSERT INTO orders
               (id, token_hash, plan_id, amount, currency, status, consent_at, consent_version, created_at)
               VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?)""",
            (order_id, token_hashed, plan_id, plan["price"] * 100, CURRENCY, created, CONSENT_VERSION, created),
        )
        row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return (dict(row) if row else None), raw_token


def get_order(order_id: str) -> dict[str, Any] | None:
    with session() as conn:
        row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not row:
            return None
        row = _expire_if_needed(conn, row)
    return dict(row)


def verify_order_token(order: dict[str, Any], raw_token: str) -> bool:
    if not raw_token or not order.get("token_hash"):
        return False
    stored = order["token_hash"]
    if stored.startswith("th_"):
        return hmac.compare_digest(stored, hash_token(raw_token))
    return hmac.compare_digest(stored, raw_token)


def _expire_if_needed(conn: sqlite3.Connection, row: sqlite3.Row) -> sqlite3.Row:
    if row["status"] != "pending":
        return row
    created = parse_dt(row["created_at"])
    if created is None or now_dt() < created + timedelta(hours=ORDER_TTL_HOURS):
        return row
    conn.execute(
        "UPDATE orders SET status = 'expired', provider_id = NULL, pay_url = NULL WHERE id = ? AND status = 'pending'",
        (row["id"],),
    )
    return conn.execute("SELECT * FROM orders WHERE id = ?", (row["id"],)).fetchone()


def set_payment(order_id: str, *, method: str, provider_id: str, pay_url: str) -> bool:
    with session() as conn:
        cur = conn.execute(
            """UPDATE orders
               SET method = ?, provider_id = ?, pay_url = ?
               WHERE id = ? AND status = 'pending'""",
            (
                method,
                secure.protect(provider_id, aad=order_id),
                secure.protect(pay_url, aad=order_id),
                order_id,
            ),
        )
        return bool(cur.rowcount)


def mark_paid(order_id: str, provider_id: str | None = None) -> bool:
    with session() as conn:
        row = conn.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not row:
            return False
        if row["status"] == "paid":
            return True
        conn.execute("UPDATE orders SET status = 'paid' WHERE id = ?", (order_id,))
    return True


def mark_failed(order_id: str, reason: str = "") -> bool:
    with session() as conn:
        row = conn.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not row or row["status"] != "pending":
            return False
        conn.execute(
            "UPDATE orders SET status = 'failed', provider_id = NULL, pay_url = NULL WHERE id = ?",
            (order_id,),
        )
    return True


def set_key(order_id: str, *, key_sub_url: str, valid_until: str, raw_token: str = "") -> bool:
    issued_at = now_iso()
    with session() as conn:
        cur = conn.execute(
            """UPDATE orders
               SET provider_id = NULL,
                   pay_url = NULL,
                   key_sub_url = ?,
                   key_valid_until = ?,
                   key_issued_at = ?
               WHERE id = ?""",
            (
                secure.protect(key_sub_url, raw_token, aad=order_id),
                valid_until,
                issued_at,
                order_id,
            ),
        )
        return bool(cur.rowcount)


def update_key_blob(order_id: str, blob: str) -> bool:
    """Перешифровывает ссылку на ключ (например, мастер-ключ → ключ клиента)."""
    with session() as conn:
        cur = conn.execute(
            "UPDATE orders SET key_sub_url = ? WHERE id = ?",
            (blob, order_id),
        )
        return bool(cur.rowcount)


def pending_with_payment(limit: int = 25) -> list[dict[str, Any]]:
    with session() as conn:
        rows = conn.execute(
            """SELECT * FROM orders
               WHERE status = 'pending' AND provider_id IS NOT NULL AND provider_id != ''
               ORDER BY created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def purge_old_orders(hours: int = 24) -> int:
    """Удаляет завершённые заказы: выданные — через `hours`, неоплаченные — через `hours`,
    неудачные — через 2 часа. Оплаченные без ключа держим 7 дней для ручного разбора.
    """
    now = now_dt()
    cutoff_issued = (now - timedelta(hours=hours)).isoformat()
    cutoff_failed = (now - timedelta(hours=2)).isoformat()
    cutoff_unpaid = (now - timedelta(hours=hours)).isoformat()
    cutoff_unissued = (now - timedelta(days=7)).isoformat()

    deleted_count = 0
    with session() as conn:
        cur = conn.execute(
            """DELETE FROM orders
               WHERE (status = 'paid' AND key_sub_url IS NOT NULL AND key_issued_at IS NOT NULL AND key_issued_at < ?)
                  OR (status IN ('failed', 'expired') AND created_at < ?)
                  OR (status = 'pending' AND created_at < ?)
                  OR (status = 'paid' AND key_sub_url IS NULL AND created_at < ?)""",
            (cutoff_issued, cutoff_failed, cutoff_unpaid, cutoff_unissued),
        )
        deleted_count = cur.rowcount

    if deleted_count > 0:
        _compact()

    return deleted_count
"""SQLite: ультра-минималистичный Zero-Knowledge буфер заказов.
Только 12 полей, шифрование ссылок клиентским токеном, затирание платежей, автоочистка 24ч.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator

from config import CURRENCY, DB_PATH, ORDER_TTL_HOURS, PLANS_BY_ID

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id              TEXT PRIMARY KEY,
    access_token    TEXT NOT NULL,
    plan_id         TEXT NOT NULL,
    amount          INTEGER NOT NULL,
    currency        TEXT NOT NULL,
    status          TEXT NOT NULL,
    method          TEXT,
    provider_id     TEXT,
    pay_url         TEXT,
    key_sub_url     TEXT,
    key_valid_until TEXT,
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
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


# ----------------- КРИПТОГРАФИЯ ZERO-KNOWLEDGE -----------------


def hash_token(raw_token: str) -> str:
    if not raw_token:
        return ""
    return "th_" + hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _keystream(key_bytes: bytes, nonce: bytes, length: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < length:
        block = hmac.new(key_bytes, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest()
        out.extend(block)
        counter += 1
    return bytes(out[:length])


def encrypt_with_token(plaintext: str, raw_token: str) -> str:
    if not plaintext or not raw_token:
        return plaintext
    nonce = secrets.token_bytes(16)
    key_bytes = hashlib.sha256(raw_token.encode("utf-8")).digest()
    data = plaintext.encode("utf-8")
    stream = _keystream(key_bytes, nonce, len(data))
    cipher = bytes(a ^ b for a, b in zip(data, stream))
    return "enc_" + base64.urlsafe_b64encode(nonce + cipher).decode("ascii")


def decrypt_with_token(ciphertext: str | None, raw_token: str) -> str | None:
    if not ciphertext:
        return None
    if not ciphertext.startswith("enc_"):
        return ciphertext
    if not raw_token:
        return None
    try:
        raw = base64.urlsafe_b64decode(ciphertext[4:].encode("ascii"))
        nonce, cipher = raw[:16], raw[16:]
        key_bytes = hashlib.sha256(raw_token.encode("utf-8")).digest()
        stream = _keystream(key_bytes, nonce, len(cipher))
        plain = bytes(a ^ b for a, b in zip(cipher, stream))
        return plain.decode("utf-8")
    except Exception:
        return None


# ----------------- РАБОТА С БАЗОЙ -----------------


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


def init_db() -> None:
    with session() as conn:
        cursor = conn.execute("PRAGMA table_info(orders)")
        cols = [row["name"] for row in cursor.fetchall()]
        if cols and len(cols) > 12:
            conn.execute("DROP TABLE orders")

        conn.executescript(SCHEMA)
        conn.execute("DROP TABLE IF EXISTS events")
        conn.execute("DROP TABLE IF EXISTS users")


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
               (id, access_token, plan_id, amount, currency, status, created_at)
               VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
            (order_id, token_hashed, plan_id, plan["price"] * 100, CURRENCY, created),
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
    if not raw_token or not order.get("access_token"):
        return False
    stored = order["access_token"]
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
            (method, provider_id, pay_url, order_id),
        )
        return bool(cur.rowcount)


def mark_checked(order_id: str) -> None:
    pass


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


def set_key(order_id: str, *, raw_token: str, key_sub_url: str, valid_until: str) -> bool:
    encrypted_url = encrypt_with_token(key_sub_url, raw_token) if raw_token else key_sub_url
    with session() as conn:
        cur = conn.execute(
            """UPDATE orders
               SET provider_id = NULL,
                   pay_url = NULL,
                   key_sub_url = ?,
                   key_valid_until = ?
               WHERE id = ?""",
            (encrypted_url, valid_until, order_id),
        )
        return bool(cur.rowcount)


def set_key_error(order_id: str, message: str) -> None:
    pass


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
    cutoff_paid = (now_dt() - timedelta(hours=hours)).isoformat()
    cutoff_failed = (now_dt() - timedelta(hours=1)).isoformat()
    with session() as conn:
        cur = conn.execute(
            """DELETE FROM orders
               WHERE created_at < ?
                  OR (status IN ('failed', 'expired') AND created_at < ?)""",
            (cutoff_paid, cutoff_failed),
        )
        count = cur.rowcount
        if count > 0:
            conn.execute("VACUUM")
        return count
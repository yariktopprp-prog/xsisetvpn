"""xsiset vpn: сайт, аккаунты, заказы и выдача ключей.

Запуск:  python app.py
Прод:    gunicorn -w 2 -b 127.0.0.1:8124 app:app  (из папки server)

Покупка: сайт создаёт заказ, сам выставляет счёт в CryptoBot или Platega,
сам сверяет оплату и после неё создаёт VLESS-клиента в панели 3x-ui.
Пользователь скачивает .txt с ключом (ссылкой-подпиской).
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict, deque
from datetime import timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from flask import (
    Flask,
    Response,
    abort,
    jsonify,
    redirect,
    request,
    send_from_directory,
    session,
)

import auth
import config
import db
import keyfile
import panel
import payments

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("xsiset")

app = Flask(__name__)
app.config.update(
    MAX_CONTENT_LENGTH=32 * 1024,
    SECRET_KEY=config.SECRET_KEY,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=config.COOKIE_SECURE,
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
)

ROOT = Path(config.BASE_DIR)
PUBLIC_FILES = {
    "index.html",
    "privacy.html",
    "style.css",
    "script.js",
    "404.html",
    "robots.txt",
}

CSP = (
    "default-src 'self'; "
    "script-src 'self' 'sha256-KJJarRUqEub4pPAihlLER8GAzKLaKGcd7AV7yMHBvgU=' https://telegram.org; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data: https://t.me https://telegram.org; "
    "connect-src 'self'; "
    "frame-src https://oauth.telegram.org https://t.me; "
    "base-uri 'none'; form-action 'self'; frame-ancestors 'none'; object-src 'none'"
)

# --- ограничители ---------------------------------------------------------

_buckets: dict[str, deque[float]] = defaultdict(deque)
_rate_lock = threading.Lock()


def _client_ip() -> str:
    if request.remote_addr in ("127.0.0.1", "::1"):
        forwarded = request.headers.get("X-Real-IP", "")
        if forwarded:
            return forwarded.strip()
    return request.remote_addr or "unknown"


def _rate(name: str, key: str, limit: int, window: int) -> bool:
    bucket_key = f"{name}:{key}"
    now = time.monotonic()
    with _rate_lock:
        bucket = _buckets[bucket_key]
        while bucket and now - bucket[0] > window:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
    return True


def _api_error(code: int, message: str) -> tuple[Response, int]:
    return jsonify({"ok": False, "error": message}), code


def _json_body() -> dict[str, Any]:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _same_origin() -> bool:
    origin = request.headers.get("Origin")
    if not origin:
        return True
    parsed = urlparse(origin)
    return parsed.netloc == request.host


@app.before_request
def _guard_writes() -> tuple[Response, int] | None:
    if request.method in ("POST", "PUT", "PATCH", "DELETE") and not _same_origin():
        return _api_error(403, "bad_origin")
    return None


@app.after_request
def _security_headers(response: Response) -> Response:
    response.headers.setdefault("Content-Security-Policy", CSP)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


# ------------------------------- страницы --------------------------------


@app.get("/")
def index() -> Response:
    return send_from_directory(ROOT, "index.html")


@app.get("/privacy")
def privacy_page() -> Response:
    return send_from_directory(ROOT, "privacy.html")


@app.get("/<path:name>")
def static_file(name: str) -> Response:
    if name in PUBLIC_FILES:
        return send_from_directory(ROOT, name)
    abort(404)


# --------------------------------- заказы --------------------------------


def _plan(plan_id: str) -> dict[str, Any] | None:
    return config.PLANS_BY_ID.get(plan_id)


def _key_payload(order: dict[str, Any], token: str) -> dict[str, Any] | None:
    if not order.get("key_sub_url"):
        return None
    return {
        "sub_url": order["key_sub_url"],
        "valid_until": order.get("key_valid_until"),
        "download_url": (
            f"/api/orders/{order['id']}/key.txt?token={token}"
            f"&lang={request.args.get('lang', 'ru')}"
        ),
    }


def _order_payload(order: dict[str, Any], token: str = "") -> dict[str, Any]:
    plan = _plan(order["plan_id"]) or {"months": order.get("months", 1)}
    key = _key_payload(order, token)
    payload: dict[str, Any] = {
        "id": order["id"],
        "plan_id": order["plan_id"],
        "months": plan["months"],
        "amount": order["amount"],
        "price": order["amount"] // 100,
        "currency": order["currency"],
        "status": order["status"],
        "method": order.get("method"),
        "asset": order.get("asset"),
        "buyer_type": order.get("buyer_type"),
        "email": order.get("email"),
        "created_at": order["created_at"],
        "expires_at": order["expires_at"],
        "payment_expires_at": order.get("payment_expires_at"),
        "paid_at": order.get("paid_at"),
        "pay_url": order.get("pay_url") if order["status"] == "pending" else None,
        "key": key,
        "key_error": order.get("key_error") if order["status"] == "paid" and not key else None,
    }
    return payload


def _can_access(order: dict[str, Any], token: str) -> bool:
    if token and order.get("access_token") and token == order["access_token"]:
        return True
    user_id = session.get("uid")
    return bool(user_id and order.get("user_id") == user_id)


_issue_lock = threading.Lock()


def _issue_key(order: dict[str, Any]) -> dict[str, Any]:
    with _issue_lock:
        fresh = db.get_order(order["id"])
        if not fresh or fresh["status"] != "paid" or fresh.get("key_issued_at"):
            return fresh or order

        plan = _plan(fresh["plan_id"]) or {"days": 30}
        try:
            issued = panel.create_client(plan["days"], fresh["id"])
        except panel.PanelError as exc:
            log.error("key issue failed for %s: %s", fresh["id"], exc)
            db.set_key_error(fresh["id"], str(exc))
            return db.get_order(fresh["id"]) or fresh

        valid_until = db.now_dt() + timedelta(days=plan["days"])
        db.set_key(
            fresh["id"],
            key_email=issued["key_email"],
            key_uuid=issued["key_uuid"],
            key_sub_id=issued["key_sub_id"],
            key_sub_url=issued["key_sub_url"],
            valid_until=valid_until.replace(microsecond=0).isoformat(),
        )
        return db.get_order(fresh["id"]) or fresh


def _refresh(order: dict[str, Any]) -> dict[str, Any]:
    if order["status"] == "pending" and order.get("provider_id"):
        checked = db.parse_dt(order.get("checked_at"))
        now = db.now_dt()
        if checked and (now - checked).total_seconds() < 3:
            return order

        db.mark_checked(order["id"])
        try:
            status = payments.invoice_status(order["method"], order["provider_id"])
        except payments.PaymentError as exc:
            log.warning("payment check failed for %s: %s", order["id"], exc)
            return order

        if status in payments.PAID_STATUSES:
            db.mark_paid(order["id"], order["provider_id"])
        elif status in payments.FAILED_STATUSES:
            db.mark_failed(order["id"], status)
        order = db.get_order(order["id"]) or order

    if order["status"] == "paid" and not order.get("key_issued_at"):
        order = _issue_key(order)

    return order


@app.get("/api/health")
def health() -> Response:
    return jsonify(
        {
            "ok": True,
            "demo": config.DEMO,
            "bot": config.BOT_USERNAME,
            "currency": config.CURRENCY,
            "payments": {
                "cryptobot": payments.cryptobot_enabled(),
                "platega": payments.platega_enabled(),
                "assets": list(config.CRYPTO_ASSETS),
            },
            "telegram_login": auth.telegram_login_ready(),
            "panel": _panel_state(),
        }
    )


_panel_cache: dict[str, Any] = {"at": 0.0, "value": None}


def _panel_state() -> dict[str, Any]:
    now = time.monotonic()
    cached = _panel_cache.get("value")
    if cached is not None and now - float(_panel_cache["at"]) < 60:
        return cached
    value = panel.probe()
    _panel_cache["at"] = now
    _panel_cache["value"] = value
    return value


@app.get("/api/plans")
def plans() -> Response:
    items = []
    for plan in config.PLANS:
        price = plan["price"]
        items.append(
            {
                "id": plan["id"],
                "months": plan["months"],
                "days": plan["days"],
                "price": price,
                "currency": config.CURRENCY,
                "per_month": round(price / plan["months"]),
                "save": plan["months"] * config.PLANS[0]["price"] - price,
            }
        )
    return jsonify({"ok": True, "plans": items})


@app.post("/api/orders")
def create_order() -> tuple[Response, int] | Response:
    ip = _client_ip()
    if not _rate("order", ip, 20, 600):
        return _api_error(429, "too_many_orders")

    body = _json_body()
    plan_id = body.get("plan_id")
    method = body.get("method")
    asset = str(body.get("asset") or "").upper() or None
    consent = body.get("consent") is True

    if not isinstance(plan_id, str) or not _plan(plan_id):
        return _api_error(400, "unknown_plan")
    if method not in ("cryptobot", "platega", "demo"):
        return _api_error(400, "unknown_method")
    if method == "cryptobot" and not payments.cryptobot_enabled():
        return _api_error(503, "cryptobot_unavailable")
    if method == "platega" and not payments.platega_enabled():
        return _api_error(503, "platega_unavailable")
    if method == "demo" and not config.DEMO:
        return _api_error(403, "demo_disabled")
    if method == "cryptobot" and asset not in config.CRYPTO_ASSETS:
        return _api_error(400, "unknown_asset")
    if not consent:
        return _api_error(400, "consent_required")

    user = auth.current_user()
    email = (body.get("email") or "").strip().lower()
    if not email and user and user.get("email"):
        email = user["email"]
    if email and not auth.valid_email(email):
        return _api_error(400, "bad_email")

    if user:
        buyer_type = "telegram" if user.get("telegram_id") else "email"
        db.set_user_consent(user["id"], ip)
    else:
        buyer_type = "anon"

    order = db.create_order(
        plan_id,
        user_id=user["id"] if user else None,
        buyer_type=buyer_type,
        email=email or None,
        consent_ip=ip,
    )
    if not order:
        return _api_error(400, "unknown_plan")

    if method != "demo":
        try:
            invoice = payments.create_invoice(order, method, asset)
        except payments.PaymentError as exc:
            log.error("invoice failed for %s: %s", order["id"], exc)
            db.mark_failed(order["id"], "invoice_failed")
            return _api_error(502, "invoice_failed")
        db.set_payment(
            order["id"],
            method=method,
            provider_id=invoice["provider_id"],
            pay_url=invoice["pay_url"],
            asset=invoice.get("asset"),
            expires_at=invoice.get("expires_at"),
        )
        order = db.get_order(order["id"]) or order
    else:
        db.set_payment(order["id"], method="demo", provider_id="demo", pay_url="")
        order = db.get_order(order["id"]) or order

    return (
        jsonify(
            {
                "ok": True,
                "order": _order_payload(order, order["access_token"]),
                "token": order["access_token"],
            }
        ),
        201,
    )


@app.get("/api/orders/<order_id>")
def order_status(order_id: str) -> Response:
    if not _rate("status", _client_ip(), 600, 600):
        return _api_error(429, "too_many_requests")
    if not order_id.isalnum() or len(order_id) > 40:
        return _api_error(400, "bad_order_id")

    order = db.get_order(order_id)
    if not order:
        return _api_error(404, "order_not_found")
    if not _can_access(order, request.args.get("token", "")):
        return _api_error(403, "forbidden")

    order = _refresh(order)
    return jsonify({"ok": True, "order": _order_payload(order, order["access_token"])})


@app.post("/api/orders/<order_id>/cancel")
def cancel_order(order_id: str) -> tuple[Response, int] | Response:
    order = db.get_order(order_id)
    if not order:
        return _api_error(404, "order_not_found")
    if not _can_access(order, request.args.get("token", "")):
        return _api_error(403, "forbidden")
    if order["status"] != "pending":
        return _api_error(409, "order_closed")
    db.mark_failed(order_id, "user_cancelled")
    return jsonify({"ok": True})


@app.post("/api/orders/<order_id>/demo-pay")
def demo_pay(order_id: str) -> tuple[Response, int] | Response:
    if not config.DEMO:
        return _api_error(403, "demo_disabled")
    if request.headers.get("X-Real-IP") or request.headers.get("X-Forwarded-For"):
        return _api_error(403, "demo_local_only")

    order = db.get_order(order_id)
    if not order:
        return _api_error(404, "order_not_found")
    if not _can_access(order, request.args.get("token", "")):
        return _api_error(403, "forbidden")
    if not db.mark_paid(order_id, "demo"):
        return _api_error(409, "order_closed")

    order = _issue_key(db.get_order(order_id))
    return jsonify({"ok": True, "order": _order_payload(order, order["access_token"])})


@app.get("/api/orders/<order_id>/key.txt")
def download_key(order_id: str) -> Response:
    order = db.get_order(order_id)
    if not order:
        abort(404)
    if not _can_access(order, request.args.get("token", "")):
        return _api_error(403, "forbidden")

    if not order.get("key_sub_url"):
        return _api_error(409, "key_not_ready")

    lang = "en" if request.args.get("lang") == "en" else "ru"
    text = keyfile.build_key_text(order, lang)
    filename = f"xsiset-vpn-{order_id}.txt"
    return Response(
        text,
        content_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@app.get("/api/orders")
def my_orders() -> Response:
    user = auth.current_user()
    if not user:
        return _api_error(401, "unauthorized")
    rows = db.list_user_orders(user["id"])
    return jsonify(
        {
            "ok": True,
            "orders": [
                _order_payload(row, row["access_token"])
                for row in rows
                if row["status"] in ("paid", "pending")
            ],
        }
    )


# ------------------------------ аккаунты ---------------------------------


@app.get("/api/auth/me")
def auth_me() -> Response:
    user = auth.current_user()
    return jsonify(
        {
            "ok": True,
            "user": auth.user_payload(user),
            "telegram_login": auth.telegram_login_ready(),
            "bot": config.BOT_USERNAME,
        }
    )


@app.post("/api/auth/register")
def auth_register() -> tuple[Response, int] | Response:
    ip = _client_ip()
    if not _rate("auth", ip, 20, 900):
        return _api_error(429, "too_many_requests")

    body = _json_body()
    email = str(body.get("email") or "").strip().lower()
    password = str(body.get("password") or "")
    consent = body.get("consent") is True

    if not auth.valid_email(email):
        return _api_error(400, "bad_email")
    if len(password) < auth.PASSWORD_MIN:
        return _api_error(400, "weak_password")
    if not consent:
        return _api_error(400, "consent_required")
    if db.get_user_by_email(email):
        return _api_error(409, "email_taken")

    user = db.create_user(
        email=email,
        password_hash=auth.hash_password(password),
        consent_ip=ip,
    )
    auth.start_session(user["id"])
    return jsonify({"ok": True, "user": auth.user_payload(user)}), 201


@app.post("/api/auth/login")
def auth_login() -> tuple[Response, int] | Response:
    ip = _client_ip()
    if not _rate("auth", ip, 20, 900):
        return _api_error(429, "too_many_requests")

    body = _json_body()
    email = str(body.get("email") or "").strip().lower()
    password = str(body.get("password") or "")

    user = db.get_user_by_email(email)
    if not user or not auth.verify_password(user.get("password_hash"), password):
        return _api_error(401, "invalid_credentials")

    db.touch_login(user["id"])
    auth.start_session(user["id"])
    return jsonify({"ok": True, "user": auth.user_payload(user)})


@app.post("/api/auth/logout")
def auth_logout() -> Response:
    auth.end_session()
    return jsonify({"ok": True})


@app.get("/api/auth/telegram/callback")
def telegram_callback() -> Response:
    """Сюда Telegram Login Widget возвращает браузер с подписанными данными."""
    data = request.args.to_dict(flat=True)
    if not auth.verify_telegram(data):
        return redirect("/?auth=fail")

    try:
        payload = auth.telegram_payload(data)
    except ValueError:
        return redirect("/?auth=fail")

    user = db.get_user_by_telegram(payload["telegram_id"])
    if user:
        db.update_user_telegram(
            user["id"],
            username=payload["telegram_username"],
            name=payload["telegram_name"],
            photo=payload["telegram_photo"],
        )
        db.set_user_consent(user["id"], _client_ip())
        user = db.get_user(user["id"])
    else:
        user = db.create_user(**payload, consent_ip=_client_ip())

    if not user:
        return redirect("/?auth=fail")

    db.touch_login(user["id"])
    auth.start_session(user["id"])
    return redirect("/?auth=ok")


# -------------------------------- служебное ------------------------------


@app.errorhandler(404)
def not_found(_error: Any) -> tuple[Response, int] | Response:
    if request.path.startswith("/api/"):
        return _api_error(404, "not_found")
    if (ROOT / "404.html").is_file():
        return send_from_directory(ROOT, "404.html"), 404
    return Response("404", status=404, mimetype="text/plain")


@app.errorhandler(500)
def server_error(_error: Any) -> tuple[Response, int] | Response:
    if request.path.startswith("/api/"):
        return _api_error(500, "server_error")
    return Response("500", status=500, mimetype="text/plain")


def _reconcile_loop() -> None:
    interval = max(30, config.RECONCILE_SECONDS)
    while True:
        time.sleep(interval)
        try:
            for order in db.pending_with_payment(15):
                _refresh(order)
        except Exception:  # noqa: BLE001 — фоновый поток не должен падать
            log.exception("payment reconcile failed")


def _start_background() -> None:
    if config.RECONCILE_SECONDS <= 0:
        return
    thread = threading.Thread(target=_reconcile_loop, name="reconcile", daemon=True)
    thread.start()


db.init_db()
_start_background()

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=False)

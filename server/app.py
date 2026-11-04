"""xsiset vpn: сайт, заказы и выдача VLESS-ключей в режиме Zero-Knowledge."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
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
    request,
    send_from_directory,
)

import config
import db
import keyfile
import panel
import payments

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("werkzeug").setLevel(logging.WARNING)
log = logging.getLogger("xsiset")

app = Flask(__name__)
app.config.update(
    MAX_CONTENT_LENGTH=32 * 1024,
    SECRET_KEY=config.SECRET_KEY,
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
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "base-uri 'none'; form-action 'self'; frame-ancestors 'none'; object-src 'none'"
)

_SALT_RAW = os.environ.get("IP_HASH_SALT", config.SECRET_KEY + "_ram_only_salt")
IP_HASH_SALT = _SALT_RAW.encode("utf-8")

_buckets: dict[str, deque[float]] = defaultdict(deque)
_rate_lock = threading.Lock()


def _ram_ip_hash() -> str:
    forwarded = request.headers.get("X-Real-IP") or request.headers.get("X-Forwarded-For")
    raw_ip = forwarded.split(",")[0].strip() if forwarded else (request.remote_addr or "unknown")
    return hmac.new(IP_HASH_SALT, raw_ip.encode("utf-8"), hashlib.sha256).hexdigest()[:16]


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
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


# ------------------------------- СТАТИКА --------------------------------


@app.get("/")
def index() -> Response:
    return send_from_directory(ROOT, "index.html")


@app.get("/privacy")
@app.get("/privacy.html")
def privacy_page() -> Response:
    return send_from_directory(ROOT, "privacy.html")


@app.get("/<path:name>")
def static_file(name: str) -> Response:
    if name in PUBLIC_FILES:
        return send_from_directory(ROOT, name)
    abort(404)


# --------------------------------- ЗАКАЗЫ --------------------------------


def _plan(plan_id: str) -> dict[str, Any] | None:
    return config.PLANS_BY_ID.get(plan_id)


def _key_payload(order: dict[str, Any], raw_token: str) -> dict[str, Any] | None:
    enc_url = order.get("key_sub_url")
    if not enc_url:
        return None
    sub_url = db.decrypt_with_token(enc_url, raw_token)
    if not sub_url:
        return None
    return {
        "sub_url": sub_url,
        "valid_until": order.get("key_valid_until"),
        "download_url": f"/api/orders/{order['id']}/key.txt?token={raw_token}&lang={request.args.get('lang', 'ru')}",
    }


def _order_payload(order: dict[str, Any], raw_token: str = "") -> dict[str, Any]:
    plan = _plan(order["plan_id"]) or {"months": 1}
    key = _key_payload(order, raw_token)
    return {
        "id": order["id"],
        "plan_id": order["plan_id"],
        "months": plan["months"],
        "amount": order["amount"],
        "price": order["amount"] // 100,
        "currency": order["currency"],
        "status": order["status"],
        "method": order.get("method"),
        "created_at": order["created_at"],
        "pay_url": order.get("pay_url") if order["status"] == "pending" else None,
        "key": key,
    }


_issue_lock = threading.Lock()


def _issue_key(order: dict[str, Any], raw_token: str) -> dict[str, Any]:
    with _issue_lock:
        fresh = db.get_order(order["id"])
        if not fresh or fresh["status"] != "paid" or fresh.get("key_sub_url"):
            return fresh or order

        plan = _plan(fresh["plan_id"]) or {"days": 30}
        try:
            issued = panel.create_client(plan["days"], fresh["id"])
        except panel.PanelError as exc:
            log.error("key issue failed for %s: %s", fresh["id"], exc)
            return db.get_order(fresh["id"]) or fresh

        valid_until = db.now_dt() + timedelta(days=plan["days"])
        db.set_key(
            fresh["id"],
            raw_token=raw_token,
            key_sub_url=issued["key_sub_url"],
            valid_until=valid_until.replace(microsecond=0).isoformat(),
        )
        return db.get_order(fresh["id"]) or fresh


def _refresh(order: dict[str, Any], raw_token: str = "") -> dict[str, Any]:
    if order["status"] == "pending" and order.get("provider_id"):
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

    if order["status"] == "paid" and not order.get("key_sub_url") and raw_token:
        order = _issue_key(order, raw_token)

    return order


@app.get("/api/health")
def health() -> Response:
    return jsonify(
        {
            "ok": True,
            "bot": config.BOT_USERNAME,
            "currency": config.CURRENCY,
            "payments": {
                "cryptobot": payments.cryptobot_enabled(),
                "platega": payments.platega_enabled(),
                "assets": list(config.CRYPTO_ASSETS),
            },
        }
    )


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
    if not _rate("order", _ram_ip_hash(), 30, 600):
        return _api_error(429, "too_many_orders")

    body = _json_body()
    plan_id = body.get("plan_id")
    method = body.get("method")
    asset = str(body.get("asset") or "").upper() or None
    consent = body.get("consent") is True

    if not isinstance(plan_id, str) or not _plan(plan_id):
        return _api_error(400, "unknown_plan")
    if method not in ("cryptobot", "platega"):
        return _api_error(400, "unknown_method")
    if method == "cryptobot" and not payments.cryptobot_enabled():
        return _api_error(503, "cryptobot_unavailable")
    if method == "platega" and not payments.platega_enabled():
        return _api_error(503, "platega_unavailable")
    if method == "cryptobot" and asset not in config.CRYPTO_ASSETS:
        return _api_error(400, "unknown_asset")
    if not consent:
        return _api_error(400, "consent_required")

    order, raw_token = db.create_order(plan_id)
    if not order:
        return _api_error(400, "unknown_plan")

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
    )
    order = db.get_order(order["id"]) or order

    return (
        jsonify(
            {
                "ok": True,
                "order": _order_payload(order, raw_token),
                "token": raw_token,
            }
        ),
        201,
    )


@app.get("/api/orders/<order_id>")
def order_status(order_id: str) -> Response:
    if not order_id.isalnum() or len(order_id) > 40:
        return _api_error(400, "bad_order_id")

    raw_token = request.args.get("token", "")
    order = db.get_order(order_id)
    if not order:
        return _api_error(404, "order_not_found")
    if not db.verify_order_token(order, raw_token):
        return _api_error(403, "forbidden")

    order = _refresh(order, raw_token)
    return jsonify({"ok": True, "order": _order_payload(order, raw_token)})


@app.post("/api/orders/<order_id>/cancel")
def cancel_order(order_id: str) -> tuple[Response, int] | Response:
    raw_token = request.args.get("token", "")
    order = db.get_order(order_id)
    if not order:
        return _api_error(404, "order_not_found")
    if not db.verify_order_token(order, raw_token):
        return _api_error(403, "forbidden")
    if order["status"] != "pending":
        return _api_error(409, "order_closed")
    db.mark_failed(order_id, "user_cancelled")
    return jsonify({"ok": True})


@app.get("/api/orders/<order_id>/key.txt")
def download_key(order_id: str) -> Response:
    raw_token = request.args.get("token", "")
    order = db.get_order(order_id)
    if not order:
        abort(404)
    if not db.verify_order_token(order, raw_token):
        return _api_error(403, "forbidden")

    decrypted_url = db.decrypt_with_token(order.get("key_sub_url"), raw_token)
    if not decrypted_url:
        return _api_error(409, "key_not_ready")

    order_copy = dict(order)
    order_copy["key_sub_url"] = decrypted_url

    lang = "en" if request.args.get("lang") == "en" else "ru"
    text = keyfile.build_key_text(order_copy, lang)
    filename = f"xsiset-vpn-{order_id}.txt"
    return Response(
        text,
        content_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@app.errorhandler(404)
def not_found(_error: Any) -> tuple[Response, int] | Response:
    if request.path.startswith("/api/"):
        return _api_error(404, "not_found")
    if (ROOT / "404.html").is_file():
        return send_from_directory(ROOT, "404.html"), 404
    return Response("404", status=404, mimetype="text/plain")


def _reconcile_loop() -> None:
    interval = max(30, config.RECONCILE_SECONDS)
    last_purge = 0.0
    while True:
        time.sleep(interval)
        try:
            for order in db.pending_with_payment(15):
                _refresh(order)

            now = time.monotonic()
            if now - last_purge > 900:
                db.purge_old_orders(hours=24)
                last_purge = now
        except Exception:
            log.exception("payment reconcile failed")


def _start_background() -> None:
    if config.RECONCILE_SECONDS <= 0:
        return
    thread = threading.Thread(target=_reconcile_loop, name="reconcile", daemon=True)
    thread.start()


db.init_db()
db.purge_old_orders(hours=24)
_start_background()

if __name__ == "__main__":
    print(f" * xsiset vpn server running on http://{config.HOST}:{config.PORT} (Production Zero-Knowledge)")
    app.run(host=config.HOST, port=config.PORT, debug=False)
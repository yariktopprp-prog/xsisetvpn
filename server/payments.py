"""Платёжные провайдеры: CryptoBot (Crypto Pay) и Platega.

Сайт сам создаёт счёт и сам сверяет статус. Никаких ключей и карточных
данных через наш бэкенд не проходит — только идентификатор счёта и ссылка
на оплату у провайдера.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import requests

import config

log = logging.getLogger(__name__)


class PaymentError(RuntimeError):
    pass


def cryptobot_enabled() -> bool:
    return config.CRYPTOPAY_READY


def platega_enabled() -> bool:
    return config.PLATEGA_READY


def _iso_or_none(epoch: int | float | None) -> str | None:
    if not epoch:
        return None
    try:
        return datetime.fromtimestamp(float(epoch), tz=timezone.utc).replace(microsecond=0).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def _order_months(order: dict[str, Any]) -> int:
    plan = config.PLANS_BY_ID.get(order.get("plan_id", ""))
    if plan and "months" in plan:
        return int(plan["months"])
    return int(order.get("months", 1))


# ------------------------------- CryptoBot -------------------------------


def _cryptobot(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not config.CRYPTOPAY_READY:
        raise PaymentError("cryptobot_not_configured")
    url = f"{config.CRYPTOPAY_API}/{path}"
    headers = {
        "Crypto-Pay-API-Token": config.CRYPTOPAY_TOKEN,
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
    except requests.RequestException as exc:
        raise PaymentError(f"cryptobot_unreachable: {exc.__class__.__name__}") from exc

    if response.status_code != 200:
        raise PaymentError(f"cryptobot_http_{response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        raise PaymentError("cryptobot_bad_json") from exc

    if not data.get("ok"):
        raise PaymentError(f"cryptobot_error: {str(data.get('error') or '')[:200]}")
    return data.get("result") or {}


def create_cryptobot(order: dict[str, Any], asset: str) -> dict[str, Any]:
    rub = order["amount"] / 100
    months = _order_months(order)
    invoice = _cryptobot(
        "createInvoice",
        {
            "currency_type": "fiat",
            "fiat": "RUB",
            "amount": f"{rub:.2f}",
            "description": f"xsiset vpn · {months} мес · {order['id']}",
            "payload": order["id"],
            "accepted_assets": asset,
            "allow_anonymous": True,
            "expires_in": config.PAYMENT_TTL_MINUTES * 60,
        },
    )

    invoice_id = invoice.get("invoice_id")
    pay_url = invoice.get("bot_invoice_url") or invoice.get("mini_app_invoice_url")
    if not invoice_id or not pay_url:
        raise PaymentError("cryptobot_bad_invoice")

    return {
        "provider_id": str(invoice_id),
        "pay_url": pay_url,
        "expires_at": _iso_or_none(invoice.get("expiration_date")),
        "asset": invoice.get("asset") or asset,
    }


def cryptobot_status(invoice_id: str) -> str:
    result = _cryptobot("getInvoices", {"invoice_ids": str(invoice_id), "count": 1})
    items = result.get("items") or []
    if not items:
        return "unknown"
    return str(items[0].get("status") or "unknown").lower()


# -------------------------------- Platega --------------------------------


def _platega_headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-MerchantId": config.PLATEGA_MERCHANT_ID,
        "X-Secret": config.PLATEGA_SECRET,
    }


def create_platega(order: dict[str, Any]) -> dict[str, Any]:
    if not config.PLATEGA_READY:
        raise PaymentError("platega_not_configured")

    rub = int(order["amount"] // 100)
    months = _order_months(order)
    payload: dict[str, Any] = {
        "paymentDetails": {"amount": rub, "currency": "RUB"},
        "description": f"xsiset vpn · {months} мес · {order['id']}",
        "payload": order["id"],
    }
    if config.PLATEGA_METHODS:
        payload["paymentMethod"] = config.PLATEGA_METHODS

    try:
        response = requests.post(
            f"{config.PLATEGA_API}/v2/transaction/process",
            headers=_platega_headers(),
            json=payload,
            timeout=25,
        )
    except requests.RequestException as exc:
        raise PaymentError(f"platega_unreachable: {exc.__class__.__name__}") from exc

    if response.status_code != 200:
        log.warning("platega create failed: %s %s", response.status_code, response.text[:200])
        raise PaymentError(f"platega_http_{response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        raise PaymentError("platega_bad_json") from exc

    pay_url = data.get("url")
    transaction_id = data.get("transactionId")
    if not pay_url or not transaction_id:
        raise PaymentError("platega_bad_invoice")

    return {
        "provider_id": str(transaction_id),
        "pay_url": pay_url,
        "expires_at": None,
        "asset": None,
    }


def platega_status(transaction_id: str) -> str:
    if not config.PLATEGA_READY:
        raise PaymentError("platega_not_configured")
    try:
        response = requests.get(
            f"{config.PLATEGA_API}/transaction/{transaction_id}",
            headers=_platega_headers(),
            timeout=20,
        )
    except requests.RequestException as exc:
        raise PaymentError(f"platega_unreachable: {exc.__class__.__name__}") from exc

    if response.status_code != 200:
        raise PaymentError(f"platega_http_{response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        raise PaymentError("platega_bad_json") from exc

    return str(data.get("status") or "unknown").lower()


PAID_STATUSES = {"paid", "success", "confirmed", "completed"}
FAILED_STATUSES = {"failed", "canceled", "cancelled", "expired", "declined"}


def create_invoice(order: dict[str, Any], method: str, asset: str | None = None) -> dict[str, Any]:
    if method == "cryptobot":
        if asset not in config.CRYPTO_ASSETS:
            asset = config.CRYPTO_ASSETS[0]
        return create_cryptobot(order, asset)
    if method == "platega":
        return create_platega(order)
    raise PaymentError("unknown_method")


def invoice_status(method: str, provider_id: str) -> str:
    if method == "cryptobot":
        return cryptobot_status(provider_id)
    if method == "platega":
        return platega_status(provider_id)
    return "unknown"
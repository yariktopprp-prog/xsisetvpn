"""Текстовый файл с ключом: то, что пользователь скачивает с сайта."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import config
from db import parse_dt


def _fmt(value: str | None) -> str:
    parsed = parse_dt(value)
    return parsed.strftime("%d.%m.%Y") if parsed else "—"


def build_key_text(order: dict[str, Any], lang: str = "ru") -> str:
    plan = config.PLANS_BY_ID.get(order["plan_id"], {})
    months = plan.get("months", order.get("months", 1))
    valid_until = order.get("key_valid_until")
    sub_url = order.get("key_sub_url") or ""
    order_id = order["id"]
    support = f"@{config.BOT_USERNAME}"

    if lang == "en":
        lines = [
            "xsiset vpn — access key",
            "=" * 46,
            "",
            f"Order:        {order_id}",
            f"Plan:         {months} month(s)",
            f"Valid until:  {_fmt(valid_until)}",
            "",
            "Your key is the subscription link below.",
            "Copy the whole line — that is the key:",
            "",
            sub_url,
            "",
            "How to connect",
            "1. Install Happ (or Streisand, v2rayNG, FoXray).",
            "2. Choose “Add subscription” and paste this link.",
            "3. Update the subscription, pick a server, turn the VPN on.",
            "",
            f"Support: {support}",
            f"Trial access is available only in the Telegram bot: {support}",
            "",
            f"Generated: {datetime.utcnow().strftime('%d.%m.%Y %H:%M')} UTC",
            "",
        ]
        return "\n".join(lines)

    lines = [
        "xsiset vpn — ключ доступа",
        "=" * 46,
        "",
        f"Заказ:        {order_id}",
        f"Тариф:        {months} мес.",
        f"Действует до: {_fmt(valid_until)}",
        "",
        "Ключ — это ссылка-подписка ниже.",
        "Скопируйте строку целиком, это и есть ключ:",
        "",
        sub_url,
        "",
        "Как подключиться",
        "1. Установите Happ (или Streisand, v2rayNG, FoXray).",
        "2. Выберите «Добавить подписку» и вставьте эту ссылку.",
        "3. Обновите подписку, выберите сервер и включите VPN.",
        "",
        f"Поддержка: {support}",
        f"Пробный период — только в Telegram-боте: {support}",
        "",
        f"Файл создан: {datetime.utcnow().strftime('%d.%m.%Y %H:%M')} UTC",
        "",
    ]
    return "\n".join(lines)

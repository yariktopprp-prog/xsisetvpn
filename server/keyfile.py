"""Формирование содержимого .txt файла с ключом доступа."""

from __future__ import annotations

from datetime import datetime, timezone
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
    now_utc = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M")

    if lang == "en":
        lines = [
            "xsiset vpn — access key",
            "=" * 46,
            "",
            f"Order ID:     {order_id}",
            f"Plan:         {months} month(s)",
            f"Valid until:  {_fmt(valid_until)}",
            "",
            "Your subscription link (copy the entire line):",
            "",
            sub_url,
            "",
            "How to connect:",
            "1. Install Happ, Streisand, v2rayNG or FoXray.",
            "2. Tap 'Add subscription' and paste this link.",
            "3. Update subscription, select a location and connect.",
            "",
            f"Support: {support}",
            f"Generated: {now_utc} UTC",
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
        "Ссылка-подписка (скопируйте строку целиком):",
        "",
        sub_url,
        "",
        "Инструкция по подключению:",
        "1. Установите приложение Happ (iOS / Android), Streisand, v2rayNG или FoXray.",
        "2. Выберите «Добавить подписку» и вставьте ссылку выше.",
        "3. Обновите список серверов и нажмите кнопку подключения.",
        "",
        f"Поддержка: {support}",
        f"Файл сформирован: {now_utc} UTC",
        "",
    ]
    return "\n".join(lines)
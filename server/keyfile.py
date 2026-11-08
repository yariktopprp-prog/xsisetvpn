"""Генерация текстового файла xsiset-vpn-{id}.txt с человекопонятной датой."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _format_date(val: str | None) -> str:
    if not val:
        return "—"
    try:
        dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return str(val)


RU_TEMPLATE = """# xsiset vpn · Конфигурация доступа
# Заказ: {order_id}
# Действует до: {valid_until}
# ----------------------------------------------------------------------

Ваша ссылка-подписка (VLESS Reality):
{sub_url}

# Инструкция по подключению:
# 1. Скопируйте ссылку выше.
# 2. Установите клиент для вашей платформы:
#    - iOS: Streisand, FoXray, V2Box
#    - Android: v2rayNG, Happ
#    - Windows: v2rayN, Nekoray
#    - macOS: FoXray, V2Box
# 3. В приложении выберите «Добавить подписку» (Add Subscription) и вставьте ссылку.
# 4. Обновите подписку — в списке появятся все 5 европейских серверов,
#    включая выделенный узел обхода списков.
#
# Поддержка: https://t.me/hkpde
"""

EN_TEMPLATE = """# xsiset vpn · Access Configuration
# Order: {order_id}
# Valid until: {valid_until}
# ----------------------------------------------------------------------

Your subscription link (VLESS Reality):
{sub_url}

# Connection guide:
# 1. Copy the link above.
# 2. Install a client for your platform:
#    - iOS: Streisand, FoXray, V2Box
#    - Android: v2rayNG, Happ
#    - Windows: v2rayN, Nekoray
#    - macOS: FoXray, V2Box
# 3. In the application, select "Add Subscription" and paste the link.
# 4. Update the subscription — all 5 European servers will appear in your list,
#    including the dedicated whitelist bypass node.
#
# Support: https://t.me/hkpde
"""


def build_key_text(order: dict[str, Any], lang: str = "ru") -> str:
    template = EN_TEMPLATE if lang == "en" else RU_TEMPLATE
    return template.format(
        order_id=order.get("id", "—"),
        valid_until=_format_date(order.get("key_valid_until")),
        sub_url=order.get("key_sub_url", "—"),
    )
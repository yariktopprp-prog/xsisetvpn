"""Клиент панели 3x-ui: выпуск и удаление VLESS-клиентов.

Панель хранит клиентов внутри JSON-поля settings каждого inbound'а,
поэтому создание — это чтение inbound'а, добавление клиента и отправка
обновлённого объекта обратно.

В режиме `dry` (нет ключей панели или явно задан XSISET_PANEL_MODE=dry)
клиенты не создаются: возвращается локальная заглушка, чтобы можно было
проверить весь сценарий без записи в боевую панель.
"""

from __future__ import annotations

import json
import logging
import secrets
import time
import uuid
from typing import Any

import requests
import urllib3

import config

if not config.PANEL_VERIFY_TLS:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

log = logging.getLogger(__name__)


class PanelError(RuntimeError):
    pass


def _api(path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if not config.PANEL_URL or not config.PANEL_TOKEN:
        raise PanelError("panel_not_configured")

    url = f"{config.PANEL_URL}{path}"
    headers = {
        "Authorization": f"Bearer {config.PANEL_TOKEN}",
        "Accept": "application/json",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"

    last_error = "panel_unreachable"
    for attempt in range(3):
        try:
            if payload is None:
                response = requests.get(
                    url, headers=headers, timeout=config.PANEL_TIMEOUT,
                    verify=config.PANEL_VERIFY_TLS,
                )
            else:
                response = requests.post(
                    url, headers=headers, json=payload, timeout=config.PANEL_TIMEOUT,
                    verify=config.PANEL_VERIFY_TLS,
                )
        except requests.RequestException as exc:
            last_error = f"panel_unreachable: {exc.__class__.__name__}"
            time.sleep(0.8 * (attempt + 1))
            continue

        if response.status_code >= 500:
            last_error = f"panel_http_{response.status_code}"
            time.sleep(0.8 * (attempt + 1))
            continue
        if response.status_code != 200:
            raise PanelError(f"panel_http_{response.status_code}")

        try:
            data = response.json()
        except ValueError as exc:
            raise PanelError("panel_bad_json") from exc

        if not data.get("success", False):
            raise PanelError(f"panel_error: {str(data.get('msg') or '')[:200]}")
        return data

    raise PanelError(last_error)


def _inbounds() -> dict[int, dict[str, Any]]:
    data = _api("/panel/api/inbounds/list")
    items = data.get("obj") or []
    return {int(item["id"]): item for item in items if "id" in item}


def _settings(inbound: dict[str, Any]) -> dict[str, Any]:
    raw = inbound.get("settings")
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PanelError("panel_bad_settings") from exc
    if isinstance(raw, dict):
        return raw
    return {}


def _update(inbound_id: int, inbound: dict[str, Any]) -> None:
    _api(f"/panel/api/inbounds/update/{inbound_id}", inbound)


def probe() -> dict[str, Any]:
    """Лёгкая проверка панели для /api/health."""
    if config.PANEL_MODE != "live" or not config.PANEL_URL or not config.PANEL_TOKEN:
        return {"mode": "dry", "ok": True, "inbounds": list(config.PANEL_INBOUND_IDS)}
    try:
        items = _inbounds()
    except PanelError as exc:
        return {"mode": "live", "ok": False, "error": str(exc)}
    found = [
        {"id": inbound_id, "remark": items[inbound_id].get("remark", "")}
        for inbound_id in config.PANEL_INBOUND_IDS
        if inbound_id in items
    ]
    return {"mode": "live", "ok": True, "inbounds": found}


def _sub_url(sub_id: str) -> str:
    base = config.PANEL_SUB_BASE or f"{config.PANEL_URL}/sub"
    return f"{base}/{sub_id}#XsisetVPN"


def create_client(days: int, tag: str) -> dict[str, Any]:
    """Создать одного клиента во всех наших inbound'ах с общим subId."""
    days = max(1, int(days))
    client_uuid = str(uuid.uuid4())
    sub_id = secrets.token_hex(8)
    key_email = f"web_{tag}"[:60]
    expiry = int((time.time() + days * 86400) * 1000)

    if not config.PANEL_LIVE:
        return {
            "key_email": key_email,
            "key_uuid": client_uuid,
            "key_sub_id": sub_id,
            "key_sub_url": f"https://panel.example/sub/dry-{sub_id}#XsisetVPN",
            "dry": True,
        }

    inbounds = _inbounds()
    targets = [inbounds[i] for i in config.PANEL_INBOUND_IDS if i in inbounds]
    if not targets:
        raise PanelError("no_inbounds")

    client = {
        "id": client_uuid,
        "flow": "",
        "email": key_email,
        "limitIp": 0,
        "totalGB": 0,
        "expiryTime": expiry,
        "enable": True,
        "tgId": 0,
        "subId": sub_id,
        "reset": 0,
    }

    updated: list[dict[str, Any]] = []
    try:
        for inbound in targets:
            settings = _settings(inbound)
            clients = settings.setdefault("clients", [])
            clients.append(dict(client))
            inbound["settings"] = json.dumps(settings, ensure_ascii=False)
            _update(int(inbound["id"]), inbound)
            updated.append(inbound)
    except PanelError:
        for inbound in updated:
            try:
                settings = _settings(inbound)
                settings["clients"] = [
                    item for item in settings.get("clients", [])
                    if item.get("email") != key_email
                ]
                inbound["settings"] = json.dumps(settings, ensure_ascii=False)
                _update(int(inbound["id"]), inbound)
            except PanelError:
                log.warning("panel rollback failed for inbound %s", inbound.get("id"))
        raise

    log.info("issued key %s in %d inbounds", key_email, len(updated))
    return {
        "key_email": key_email,
        "key_uuid": client_uuid,
        "key_sub_id": sub_id,
        "key_sub_url": _sub_url(sub_id),
        "dry": False,
    }


def delete_client(key_email: str) -> bool:
    """Удалить клиента во всех inbound'ах (возврат, отмена, чистка тестов)."""
    if not config.PANEL_LIVE:
        return True
    if not key_email:
        return False

    inbounds = _inbounds()
    removed = False
    for inbound_id in config.PANEL_INBOUND_IDS:
        inbound = inbounds.get(inbound_id)
        if not inbound:
            continue
        settings = _settings(inbound)
        clients = settings.get("clients", [])
        kept = [item for item in clients if item.get("email") != key_email]
        if len(kept) == len(clients):
            continue
        settings["clients"] = kept
        inbound["settings"] = json.dumps(settings, ensure_ascii=False)
        _update(inbound_id, inbound)
        removed = True
    return removed

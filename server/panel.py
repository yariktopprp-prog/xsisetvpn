"""3x-ui API: создание клиентов на всех нодах и сервере обхода списков."""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

import paramiko
import requests

log = logging.getLogger("xsiset.panel")

# =======================================================
# НАСТРОЙКИ СВЯЗИ С МАСТЕР-ПАНЕЛЬЮ И НОДАМИ
# =======================================================
SERVER_DOMAIN = "xsisetsweden3x-ui1.site"
SUB_PORT = 2096

MASTER_PANEL_URL = "https://xsisetsweden3x-ui1.site:2053/D9ydIMzezNyS7e3TsM"
MASTER_API_TOKEN = "IV4w9vkTKL6L332Lc2h7wIKrasdvHLqIgQmI7kLJkDLPMsvi"

SSH_HOST = "31.76.81.35"
SSH_USER = "root"
SSH_PASSWORD = "BhqYaV62La77zMM"

GB = 1024 * 1024 * 1024
LIMIT_GB_PER_MONTH = 20
LIMITED_INBOUND_IDS = {17}


class PanelError(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {MASTER_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def is_limited_inbound(inbound_obj: dict[str, Any]) -> bool:
    """Инбаунд обхода списков (лимит 20 ГБ/мес на ID 17 или по слову 'обход')."""
    remark = str(inbound_obj.get("remark", "")).lower()
    inb_id = int(inbound_obj.get("id", 0))
    return "обход" in remark or inb_id in LIMITED_INBOUND_IDS


def format_comment(used_gb: float, total_gb: int) -> str:
    return f"[{used_gb:.2f}/{total_gb} ГБ]"


def _run_untmp_ssh() -> None:
    """Подключается по SSH и выполняет /root/untmp.sh для фиксации обхода в подписке."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASSWORD, timeout=10)
        _, stdout, stderr = ssh.exec_command("/root/untmp.sh", timeout=25)
        exit_code = stdout.channel.recv_exit_status()
        err_text = stderr.read().decode("utf-8", errors="ignore").strip()
        if exit_code != 0 or err_text:
            log.warning("[untmp.sh] code=%s, stderr=%s", exit_code, err_text)
        else:
            log.info("[untmp.sh] _tmp успешно снят, обход добавлен в подписку")
    except Exception as exc:
        log.error("[untmp.sh] ошибка SSH: %s", exc)
    finally:
        ssh.close()


def _add_client_to_inbounds(client_data: dict[str, Any], inbound_ids: list[int]) -> bool:
    """Привязывает клиента сразу ко всем переданным инбаундам."""
    if not inbound_ids:
        return False

    panel_url = MASTER_PANEL_URL.rstrip("/")
    v3_add_url = f"{panel_url}/panel/api/clients/add"
    v3_payload = {
        "client": client_data,
        "inboundIds": inbound_ids,
    }

    try:
        resp = requests.post(v3_add_url, json=v3_payload, headers=_headers(), timeout=12)
        if resp.status_code == 200:
            res_json = resp.json()
            if res_json.get("success"):
                log.info("Клиент %s привязан к инбаундам %s", client_data["email"], inbound_ids)
                return True
            log.warning("clients/add отклонил %s: %s", client_data["email"], res_json.get("msg"))
    except Exception as exc:
        log.warning("Ошибка clients/add: %s. Пробуем поочерёдный addClient", exc)

    # Резервный метод поочередного добавления, если clients/add не сработал
    success_any = False
    add_client_url = f"{panel_url}/panel/api/inbounds/addClient"
    for inb_id in inbound_ids:
        payload = {
            "id": inb_id,
            "settings": json.dumps({"clients": [client_data]}),
        }
        try:
            r = requests.post(add_client_url, json=payload, headers=_headers(), timeout=10)
            if r.status_code == 200 and r.json().get("success"):
                success_any = True
                log.info("addClient успешно: %s -> Inbound %s", client_data["email"], inb_id)
            else:
                log.error("Inbound %s отклонил клиента %s", inb_id, client_data["email"])
        except Exception as exc:
            log.error("Сбой запроса к Inbound %s: %s", inb_id, exc)

    return success_any


def create_client(days: int, order_id: str) -> dict[str, str]:
    """
    Создает клиента на ВСЕХ активных инбаундах панели (все европейские ноды + обход).
    """
    panel_url = MASTER_PANEL_URL.rstrip("/")
    api_list_url = f"{panel_url}/panel/api/inbounds/list"

    try:
        resp = requests.get(api_list_url, headers=_headers(), timeout=15)
        resp.raise_for_status()
        data = resp.json()
        all_inbounds = data.get("obj", [])
    except Exception as exc:
        raise PanelError(f"Не удалось получить список инбаундов: {exc}") from exc

    active_inbounds = [inb for inb in all_inbounds if inb.get("enable", True)]
    if not active_inbounds:
        raise PanelError("Нет активных инбаундов в панели")

    unlimited_inbound_ids: list[int] = []
    limited_inbound_ids: list[int] = []
    unlimited_flow = ""

    for inb in active_inbounds:
        inb_id = int(inb["id"])
        if is_limited_inbound(inb):
            limited_inbound_ids.append(inb_id)
        else:
            unlimited_inbound_ids.append(inb_id)
            if not unlimited_flow:
                settings = inb["settings"]
                if isinstance(settings, str):
                    try:
                        settings = json.loads(settings)
                    except Exception:
                        settings = {}
                clients = settings.get("clients", [])
                if clients:
                    unlimited_flow = clients[0].get("flow", "")

    # Расчет срока и лимитов трафика
    months = max(1, round(days / 30))
    total_gb_num = months * LIMIT_GB_PER_MONTH
    limit_bytes = total_gb_num * GB
    expiry = int((time.time() + (days * 86400)) * 1000)

    unique_id = uuid.uuid4().hex[:10]
    shared_sub_id = uuid.uuid4().hex[:16]
    temp_sub_id = f"{shared_sub_id}_tmp"
    shared_uuid = str(uuid.uuid4())

    cdn_email = f"web_{order_id[:6]}_{unique_id}_cdn"
    main_email = f"web_{order_id[:6]}_{unique_id}_main"

    # 1. Добавляем _cdn на инбаунд обхода с временным subId
    if limited_inbound_ids:
        limited_client = {
            "id": shared_uuid,
            "flow": "",
            "email": cdn_email,
            "limitIp": 0,
            "totalGB": limit_bytes,
            "expiryTime": expiry,
            "enable": True,
            "tgId": 0,
            "subId": temp_sub_id,
            "comment": format_comment(0.0, total_gb_num),
            "reset": 0,
        }
        _add_client_to_inbounds(limited_client, limited_inbound_ids)

    # 2. Добавляем _main на все остальные европейские регионы
    unlimited_client = {
        "id": shared_uuid,
        "flow": unlimited_flow,
        "email": main_email,
        "limitIp": 0,
        "totalGB": 0,
        "expiryTime": expiry,
        "enable": True,
        "tgId": 0,
        "subId": shared_sub_id,
        "comment": "",
        "reset": 0,
    }
    ok = _add_client_to_inbounds(unlimited_client, unlimited_inbound_ids)
    if not ok:
        raise PanelError("Не удалось привязать клиента к основным серверам")

    # 3. Синхронизируем базу через скрипт untmp.sh на сервере
    if limited_inbound_ids:
        time.sleep(1.5)
        _run_untmp_ssh()

    sub_url = f"https://{SERVER_DOMAIN}:{SUB_PORT}/sub/{shared_sub_id}#XsisetVPN"

    return {
        "key_email": main_email,
        "key_uuid": shared_uuid,
        "key_sub_id": shared_sub_id,
        "key_sub_url": sub_url,
    }


def probe() -> dict[str, Any]:
    """Проверка доступности мастер-панели."""
    try:
        r = requests.get(
            f"{MASTER_PANEL_URL.rstrip('/')}/panel/api/inbounds/list",
            headers=_headers(),
            timeout=5,
        )
        return {"online": r.status_code == 200}
    except Exception as exc:
        return {"online": False, "error": str(exc)}
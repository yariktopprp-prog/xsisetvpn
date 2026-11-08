"""3x-ui API: создание клиентов на всех нодах без хардкода секретов.

Любая ошибка сети, HTTP или ответа панели превращается в PanelError.
Основной клиент добавляется сразу во все обычные inbound'ы. Для узла обхода
(whitelist) создаётся отдельный клиент с лимитом трафика, но с общим subId,
поэтому обе группы серверов попадают в одну ссылку-подписку.

Основной путь — как в прежнем боте: клиент обхода создаётся с временным
subId `<id>_tmp`, основной — с настоящим, затем по SSH выполняется
`/root/untmp.sh`, который убирает `_tmp` и перезапускает x-ui. Если SSH не
настроен, используется резервная схема: оба клиента отправляются
одновременно (проверка занятости subId в панели не транзакционная).

Создание атомарное: при любом сбое удаляются оба клиента через
POST /panel/api/clients/del/{email}.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import requests

import config

try:  # SSH нужен только для старой схемы untmp; без него работает резервная.
    import paramiko
except ImportError:  # pragma: no cover - на сервере зависимость ставится из requirements
    paramiko = None

log = logging.getLogger("xsiset.panel")


class PanelError(RuntimeError):
    pass


def _mode() -> str:
    return config.PANEL_MODE


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {config.PANEL_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _request(method: str, url: str, *, json_body: Any = None, timeout: int | None = None) -> dict[str, Any]:
    """Единая точка запросов: сеть, HTTP-код и JSON строго проверяются."""
    try:
        response = requests.request(
            method,
            url,
            json=json_body,
            headers=_headers(),
            timeout=timeout or config.PANEL_TIMEOUT,
            verify=config.PANEL_VERIFY_TLS,
        )
    except requests.RequestException as exc:
        raise PanelError(f"Сбой связи с панелью: {exc}") from exc

    if response.status_code != 200:
        raise PanelError(f"Панель ответила HTTP {response.status_code}")

    try:
        payload = response.json()
    except ValueError as exc:
        raise PanelError("Панель вернула не-JSON ответ") from exc

    if not isinstance(payload, dict):
        raise PanelError("Неожиданный ответ панели")
    if payload.get("success") is False:
        raise PanelError(str(payload.get("msg") or "панель отклонила запрос"))
    return payload


def _delete_client_by_email(email: str) -> None:
    """Откат: удаление клиента по всем inbound'ам (подтверждённый endpoint)."""
    if _mode() == "dry" or not config.PANEL_URL:
        return
    try:
        _request(
            "POST",
            f"{config.PANEL_URL}/panel/api/clients/del/{email}",
            timeout=10,
        )
    except PanelError as exc:
        log.warning("Не удалось удалить клиента %s при откате: %s", email, exc)


def _sub_url(shared_sub_id: str) -> str:
    base = config.PANEL_SUB_BASE.rstrip("/")
    if not base:
        base = f"https://{config.PANEL_DOMAIN}:{config.PANEL_SUB_PORT}"
    if not base.endswith("/sub"):
        base += "/sub"
    return f"{base}/{shared_sub_id}#XsisetVPN"


def _load_inbounds() -> list[int]:
    payload = _request("GET", f"{config.PANEL_URL}/panel/api/inbounds/list")
    raw = payload.get("obj")
    if not isinstance(raw, list):
        raise PanelError("Панель не вернула список серверов")

    ids: list[int] = []
    for inb in raw:
        if not isinstance(inb, dict) or not inb.get("enable", True):
            continue
        try:
            inb_id = int(inb.get("id", 0))
        except (TypeError, ValueError):
            continue
        if config.PANEL_INBOUND_IDS and inb_id not in config.PANEL_INBOUND_IDS:
            continue
        ids.append(inb_id)

    if not ids:
        raise PanelError("Нет доступных серверов в панели")
    return ids


def _client_payload(email: str, client_uuid: str, sub_id: str, total_gb: int, expiry: int) -> dict[str, Any]:
    return {
        "id": client_uuid,
        "flow": "",
        "email": email,
        "limitIp": 0,
        "totalGB": total_gb,
        "expiryTime": expiry,
        "enable": True,
        "tgId": 0,
        "subId": sub_id,
        "comment": "",
        "reset": 0,
    }


def _add_client(
    email: str,
    client_uuid: str,
    sub_id: str,
    total_gb: int,
    expiry: int,
    inbound_ids: list[int],
) -> None:
    _request(
        "POST",
        f"{config.PANEL_URL}/panel/api/clients/add",
        json_body={
            "client": _client_payload(email, client_uuid, sub_id, total_gb, expiry),
            "inboundIds": inbound_ids,
        },
    )


def _add_clients_at_once(requests: list[tuple[str, str, str, int, int, list[int]]]) -> None:
    """Создать двух клиентов с общим subId одновременным запросом.

    По отдельности второй /clients/add отклоняется ошибкой «Duplicate subId»,
    но проверка занятости subId в панели не транзакционная. Пара клиентов,
    отправленная одновременно, создаётся с одним subId и остаётся такой:
    subId хранится в записи каждого клиента, поэтому фоновая синхронизация
    inbound'ов его не откатывает. Именно так выдавались прежние ключи
    (main + лимитный cdn с общей подпиской).
    """
    if len(requests) == 1:
        _add_client(*requests[0])
        return

    barrier = threading.Barrier(len(requests))

    def worker(args: tuple[str, str, str, int, int, list[int]]) -> None:
        barrier.wait(timeout=10)
        _add_client(*args)

    with ThreadPoolExecutor(max_workers=len(requests)) as pool:
        futures = [pool.submit(worker, args) for args in requests]
        errors: list[BaseException] = []
        for future in futures:
            try:
                future.result()
            except BaseException as exc:  # noqa: BLE001 - пробрасываем первую ошибку
                errors.append(exc)
        if errors:
            first = errors[0]
            raise PanelError(str(first)) from first


def _untmp_available() -> bool:
    return bool(
        _mode() == "live"
        and config.PANEL_SSH_HOST
        and config.PANEL_SSH_PASSWORD
        and paramiko is not None
    )


def _run_untmp() -> bool:
    """Запустить /root/untmp.sh так же, как это делает старый бот.

    Скрипт перезапускает x-ui, поэтому SSH-сессия обрывается и код возврата
    приходит как -1. Команду запускаем через nohup и не ждём её завершения;
    результат проверяется по subId клиента в панели.
    """
    if not _untmp_available():
        return False
    ssh = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            config.PANEL_SSH_HOST,
            port=config.PANEL_SSH_PORT,
            username=config.PANEL_SSH_USER,
            password=config.PANEL_SSH_PASSWORD,
            timeout=10,
            banner_timeout=15,
            auth_timeout=15,
        )
        command = (
            f"nohup bash {config.PANEL_UNTMP_CMD} "
            ">/tmp/xsiset_untmp.log 2>&1 & echo STARTED"
        )
        _stdin, stdout, _stderr = ssh.exec_command(command, timeout=15)
        marker = stdout.readline().strip()
        if marker != "STARTED":
            log.warning("untmp не запустился: %s", marker[:200])
            return False
        log.info("untmp запущен")
        return True
    except Exception as exc:  # noqa: BLE001 - SSH не должен ломать выдачу
        log.warning("Не удалось запустить untmp по SSH: %s", exc)
        return False
    finally:
        if ssh is not None:
            try:
                ssh.close()
            except Exception:
                pass


def _wait_sub_id(email: str, sub_id: str, timeout: int = 25) -> bool:
    """Дождаться, пока untmp заменит временный subId на общий."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            payload = _request("GET", f"{config.PANEL_URL}/panel/api/inbounds/list", timeout=10)
            for inb in payload.get("obj") or []:
                if not isinstance(inb, dict):
                    continue
                settings = inb.get("settings")
                if isinstance(settings, str):
                    try:
                        settings = json.loads(settings)
                    except ValueError:
                        continue
                if not isinstance(settings, dict):
                    continue
                for client in settings.get("clients") or []:
                    if client.get("email") == email and client.get("subId") == sub_id:
                        return True
        except PanelError:
            pass  # панель перезапускается
        time.sleep(1)
    return False


def _add_pair_legacy(
    main_email: str,
    limited_email: str,
    shared_uuid: str,
    shared_sub_id: str,
    limit_bytes: int,
    expiry: int,
    main_ids: list[int],
    limited_ids: list[int],
) -> None:
    """Старая схема: _cdn с временным subId, _main с общим, затем untmp.

    Пока у клиента обхода subId оканчивается на `_tmp`, панель не считает его
    дублем. Поэтому оба клиента создаются последовательно и получают один
    subId после untmp — ровно как выдавал прежний бот.
    """
    temp_sub_id = f"{shared_sub_id}_tmp"
    _add_client(limited_email, shared_uuid, temp_sub_id, limit_bytes, expiry, limited_ids)
    try:
        _add_client(main_email, shared_uuid, shared_sub_id, 0, expiry, main_ids)
        time.sleep(1.5)  # даём панели синхронизировать клиента с нодой
        if not _run_untmp():
            raise PanelError("untmp не запущен")
        if not _wait_sub_id(limited_email, shared_sub_id):
            raise PanelError("untmp не заменил временный subId")
    except PanelError:
        _delete_client_by_email(limited_email)
        raise


def create_client(days: int, order_id: str, months: int | None = None) -> dict[str, str]:
    if _mode() == "dry" or not config.PANEL_URL or not config.PANEL_TOKEN:
        mock_sub = uuid.uuid4().hex[:16]
        log.info("[DRY] Создан мок-ключ для заказа %s", order_id)
        return {
            "key_email": f"dry_{order_id[:6]}_main",
            "key_uuid": str(uuid.uuid4()),
            "key_sub_id": mock_sub,
            "key_sub_url": _sub_url(mock_sub),
        }

    all_inbounds = _load_inbounds()
    limited_ids = [inb_id for inb_id in all_inbounds if inb_id in config.PANEL_LIMITED_IDS]
    main_ids = [inb_id for inb_id in all_inbounds if inb_id not in config.PANEL_LIMITED_IDS]
    if not main_ids:
        # Если все ноды помечены лимитными, основной клиент создаётся на всех.
        main_ids, limited_ids = all_inbounds, []

    expiry = int((time.time() + days * 86400) * 1000)
    period_months = months if months and months > 0 else max(1, round(days / 30))
    limit_bytes = int(period_months * config.LIMIT_GB_PER_MONTH * 1024**3)

    last_error: PanelError | None = None
    for attempt in range(3):
        shared_sub_id = uuid.uuid4().hex[:16]
        shared_uuid = str(uuid.uuid4())
        suffix = uuid.uuid4().hex[:10]
        email = f"web_{order_id[:6]}_{suffix}_main"
        limited_email = f"web_{order_id[:6]}_{suffix}_cdn"

        try:
            if limited_ids and _untmp_available():
                try:
                    _add_pair_legacy(
                        email,
                        limited_email,
                        shared_uuid,
                        shared_sub_id,
                        limit_bytes,
                        expiry,
                        main_ids,
                        limited_ids,
                    )
                    log.info("Заказ %s: ключ выдан старой схемой (_tmp + untmp)", order_id)
                    return {
                        "key_email": email,
                        "key_uuid": shared_uuid,
                        "key_sub_id": shared_sub_id,
                        "key_sub_url": _sub_url(shared_sub_id),
                    }
                except PanelError as exc:
                    last_error = exc
                    _delete_client_by_email(limited_email)
                    _delete_client_by_email(email)
                    log.warning(
                        "Заказ %s: старая схема не сработала (%s), резервная",
                        order_id,
                        exc,
                    )
                    time.sleep(0.5)

            if limited_ids:
                _add_clients_at_once(
                    [
                        (email, shared_uuid, shared_sub_id, 0, expiry, main_ids),
                        (limited_email, shared_uuid, shared_sub_id, limit_bytes, expiry, limited_ids),
                    ]
                )
            else:
                _add_client(email, shared_uuid, shared_sub_id, 0, expiry, main_ids)
            return {
                "key_email": email,
                "key_uuid": shared_uuid,
                "key_sub_id": shared_sub_id,
                "key_sub_url": _sub_url(shared_sub_id),
            }
        except PanelError as exc:
            last_error = exc
            # Панель могла применить запрос частично — удаляем оба возможных клиента.
            _delete_client_by_email(limited_email)
            _delete_client_by_email(email)
            log.warning("Попытка выдачи %s/%s не удалась: %s", order_id, attempt + 1, exc)
            time.sleep(0.5)

    raise last_error or PanelError("Не удалось создать клиентов в панели")


def probe() -> dict[str, Any]:
    if _mode() == "dry":
        return {"online": True, "mode": "dry"}
    if not config.PANEL_URL or not config.PANEL_TOKEN:
        return {"online": False, "error": "panel_not_configured"}
    try:
        _request("GET", f"{config.PANEL_URL}/panel/api/inbounds/list", timeout=5)
        return {"online": True, "mode": "live"}
    except PanelError as exc:
        return {"online": False, "error": str(exc)}

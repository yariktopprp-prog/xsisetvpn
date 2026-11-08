"""Шифрование чувствительных полей БД (AES-256-GCM).

Две схемы:
  v1 — мастер-ключ сервера (нужен фоновой выдаче ключа, когда токена ещё нет);
  v2 — ключ, производный от токена доступа клиента (после первого обращения).

Ссылка VLESS и платёжные реквизиты никогда не хранятся в открытом виде.
"""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import config

_MASTER_KEY = hashlib.sha256(
    b"xsiset-vpn:data-key:v1:" + config.SECRET_KEY.encode("utf-8")
).digest()
_TOKEN_LABEL = b"xsiset-vpn:order-key:v1:"
_DEFAULT_AAD = b"xsiset-vpn:field"
_NONCE = 12


class DecryptError(RuntimeError):
    pass


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64d(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def _aad(aad: str | None) -> bytes:
    return (aad or "").encode("utf-8") if aad else _DEFAULT_AAD


def _token_key(raw_token: str) -> bytes:
    return hashlib.sha256(_TOKEN_LABEL + raw_token.encode("utf-8")).digest()


def _encrypt(key: bytes, plaintext: str, aad: str | None) -> str:
    nonce = os.urandom(_NONCE)
    sealed = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), _aad(aad))
    return _b64e(nonce) + ":" + _b64e(sealed)


def _decrypt(key: bytes, blob: str, aad: str | None) -> str:
    nonce_s, data_s = blob.split(":", 1)
    return AESGCM(key).decrypt(_b64d(nonce_s), _b64d(data_s), _aad(aad)).decode("utf-8")


def is_encrypted(value: str | None) -> bool:
    return bool(value) and (value.startswith("v1:") or value.startswith("v2:"))


def is_token_bound(value: str | None) -> bool:
    return bool(value) and value.startswith("v2:")


def encrypt_master(plaintext: str, aad: str | None = None) -> str:
    return "v1:" + _encrypt(_MASTER_KEY, plaintext, aad)


def decrypt_master(blob: str, aad: str | None = None) -> str:
    if not blob or not blob.startswith("v1:"):
        raise DecryptError("not_master_blob")
    return _decrypt(_MASTER_KEY, blob[3:], aad)


def encrypt_for_token(plaintext: str, raw_token: str, aad: str | None = None) -> str:
    if not raw_token:
        raise DecryptError("empty_token")
    return "v2:" + _encrypt(_token_key(raw_token), plaintext, aad)


def decrypt_for_token(blob: str, raw_token: str, aad: str | None = None) -> str:
    if not blob or not blob.startswith("v2:"):
        raise DecryptError("not_token_blob")
    if not raw_token:
        raise DecryptError("empty_token")
    return _decrypt(_token_key(raw_token), blob[3:], aad)


def protect(value: str | None, raw_token: str = "", aad: str | None = None) -> str | None:
    """Шифрует непустое значение: токеном клиента, если он известен, иначе мастер-ключом."""
    if not value:
        return value
    if is_encrypted(value):
        return value
    if raw_token:
        return encrypt_for_token(value, raw_token, aad)
    return encrypt_master(value, aad)


def reveal(value: str | None, raw_token: str = "", aad: str | None = None) -> str | None:
    """Расшифровывает значение. Для v1 нужен мастер-ключ, для v2 — токен клиента."""
    if not value:
        return value
    if not is_encrypted(value):
        # легаси-значение до миграции: считаем открытым
        return value
    try:
        if value.startswith("v2:"):
            return decrypt_for_token(value, raw_token, aad)
        text = decrypt_master(value, aad)
        return text
    except Exception:
        return None

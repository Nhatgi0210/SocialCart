import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from shared.auth import AuthError
from shared.config import settings


def cipher():
    try:
        key = bytes.fromhex(settings.encryption_key)
        if len(key) != 32:
            raise ValueError
    except ValueError:
        raise AuthError(503, "CONFIG_REQUIRED", "Cần ENCRYPTION_KEY gồm 64 ký tự hex ở backend") from None
    return AESGCM(key)


def encrypt(value: str) -> str:
    nonce = os.urandom(12)
    return base64.b64encode(nonce + cipher().encrypt(nonce, value.encode(), b"socialcart-platform-v1")).decode()


def decrypt(value: str | None) -> str:
    try:
        encoded = base64.b64decode(value or "", validate=True)
        return cipher().decrypt(encoded[:12], encoded[12:], b"socialcart-platform-v1").decode()
    except AuthError:
        raise
    except Exception:
        raise AuthError(503, "TOKEN_UNAVAILABLE", "Cần kết nối lại tài khoản nền tảng") from None

"""安全工具：密码哈希、JWT、AES-GCM 密钥加密。"""
import base64
import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


# ---------- 密码哈希 ----------

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


# ---------- JWT ----------

def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


# ---------- API Key 加密（AES-256-GCM） ----------

def _aes_key() -> bytes:
    # 将任意长度密钥规范化到 32 字节
    return hashlib.sha256(settings.AES_KEY.encode("utf-8")).digest()


def encrypt_api_key(plain: str) -> str:
    nonce = os.urandom(12)
    ciphertext = AESGCM(_aes_key()).encrypt(nonce, plain.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("utf-8")


def decrypt_api_key(encrypted: str) -> str:
    raw = base64.b64decode(encrypted)
    nonce, ciphertext = raw[:12], raw[12:]
    plain = AESGCM(_aes_key()).decrypt(nonce, ciphertext, None)
    return plain.decode("utf-8")

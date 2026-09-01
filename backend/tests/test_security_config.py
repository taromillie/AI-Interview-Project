# -*- coding: utf-8 -*-
"""生产密钥强校验测试：默认密钥无法用于生产启动，开发模式仅告警。

覆盖验收标准：默认密钥无法用于生产启动。
"""
import warnings

import pytest

from app.core.config import DEFAULT_AES_KEY, DEFAULT_JWT_SECRET, Settings

STRONG_JWT = "prod-jwt-secret-" + "x" * 40
STRONG_AES = "prod-aes-key-" + "y" * 32


def test_production_rejects_default_secrets():
    """DEBUG=false + 默认密钥 → 拒绝启动。"""
    with pytest.raises(ValueError, match="默认密钥"):
        Settings(
            DEBUG=False,
            JWT_SECRET=DEFAULT_JWT_SECRET,
            AES_KEY=DEFAULT_AES_KEY,
            _env_file=None,
        )


def test_production_rejects_weak_jwt_secret():
    """DEBUG=false + 过短 JWT_SECRET → 拒绝启动。"""
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings(
            DEBUG=False,
            JWT_SECRET="short",
            AES_KEY=STRONG_AES,
            _env_file=None,
        )


def test_production_rejects_weak_aes_key():
    """DEBUG=false + 过短 AES_KEY → 拒绝启动。"""
    with pytest.raises(ValueError, match="AES_KEY"):
        Settings(
            DEBUG=False,
            JWT_SECRET=STRONG_JWT,
            AES_KEY="too-short",
            _env_file=None,
        )


def test_production_accepts_strong_secrets():
    """DEBUG=false + 强密钥 → 正常加载。"""
    s = Settings(
        DEBUG=False,
        JWT_SECRET=STRONG_JWT,
        AES_KEY=STRONG_AES,
        _env_file=None,
    )
    assert s.DEBUG is False
    assert s.JWT_SECRET == STRONG_JWT
    assert s.AES_KEY == STRONG_AES


def test_dev_allows_default_secrets_with_warning():
    """DEBUG=true + 默认密钥 → 允许启动，同时发出告警提示。"""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        s = Settings(
            DEBUG=True,
            JWT_SECRET=DEFAULT_JWT_SECRET,
            AES_KEY=DEFAULT_AES_KEY,
            _env_file=None,
        )
    assert s.DEBUG is True
    assert any(issubclass(w.category, UserWarning) and "默认密钥" in str(w.message) for w in caught)

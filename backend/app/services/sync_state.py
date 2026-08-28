"""岗位同步状态管理：动态同步间隔 + 最近同步时间，持久化到 data/sync_config.json。

设计说明：
- 间隔可在前端动态调整（10/30/60 分钟或仅手动），重启后端后仍生效；
- 调度线程每 60 秒 tick 一次，根据 last_sync_at + interval 判断是否需要同步；
- 所有读写均加锁，避免并发；文件损坏/不可写时降级为内存态。
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

# 配置文件放在后端 data 目录下（与向量库同级）
_STATE_FILE = Path(settings.VECTOR_DB_PATH).resolve().parent / "sync_config.json"

_lock = threading.Lock()

_state: dict = {
    "auto_enabled": True,
    "interval_minutes": max(int(settings.JOB_SYNC_INTERVAL_HOURS * 60), 1) or 30,
    "last_sync_at": None,   # ISO 时间字符串
    "next_sync_at": None,   # ISO 时间字符串
    "last_sync_stats": None,
}


def _load() -> None:
    try:
        if not _STATE_FILE.exists():
            return
        data = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            _state.update({k: v for k, v in data.items() if k in _state})
    except Exception as exc:  # 文件损坏/无权限 → 使用默认值
        logger.warning("同步配置文件读取失败，使用默认值: %s", exc)


def _save() -> None:
    try:
        _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _STATE_FILE.write_text(json.dumps(_state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.warning("同步配置持久化失败（仅本次内存生效）: %s", exc)


def _recompute_next() -> None:
    if not _state.get("auto_enabled"):
        _state["next_sync_at"] = None
        return
    base = _state.get("last_sync_at")
    try:
        base_dt = datetime.fromisoformat(base) if base else datetime.now()
    except (ValueError, TypeError):
        base_dt = datetime.now()
    interval = max(int(_state.get("interval_minutes", 30) or 30), 1)
    _state["next_sync_at"] = (base_dt + timedelta(minutes=interval)).isoformat(timespec="seconds")


def get_sync_state() -> dict:
    """返回当前同步状态（含下次自动同步时间）。"""
    with _lock:
        if _state.get("_loaded") is None:
            _load()
            _state["_loaded"] = True
            _recompute_next()
        return {
            "auto_enabled": bool(_state.get("auto_enabled", True)),
            "interval_minutes": int(_state.get("interval_minutes", 30) or 30),
            "last_sync_at": _state.get("last_sync_at"),
            "next_sync_at": _state.get("next_sync_at"),
            "last_sync_stats": _state.get("last_sync_stats"),
        }


def update_sync_config(interval_minutes: int | None = None, auto_enabled: bool | None = None) -> dict:
    """动态调整同步配置并持久化。返回更新后的状态。"""
    with _lock:
        if _state.get("_loaded") is None:
            _load()
            _state["_loaded"] = True
        if interval_minutes is not None:
            minutes = max(int(interval_minutes), 5)  # 最短 5 分钟，防止对数据源压力过大
            _state["interval_minutes"] = minutes
        if auto_enabled is not None:
            _state["auto_enabled"] = bool(auto_enabled)
        _recompute_next()
        _save()
    return get_sync_state()


def record_sync_done(stats: dict) -> dict:
    """同步完成后记录时间戳并推进下次同步计划。"""
    with _lock:
        if _state.get("_loaded") is None:
            _load()
            _state["_loaded"] = True
        now = datetime.now()
        _state["last_sync_at"] = now.isoformat(timespec="seconds")
        _state["last_sync_stats"] = stats
        _recompute_next()
        _save()
    return get_sync_state()


def is_sync_due() -> bool:
    """调度线程判断：是否到了自动同步时间。"""
    with _lock:
        if _state.get("_loaded") is None:
            _load()
            _state["_loaded"] = True
            _recompute_next()
        if not _state.get("auto_enabled", True):
            return False
        last = _state.get("last_sync_at")
        if not last:
            return True  # 从未同步过
        try:
            last_dt = datetime.fromisoformat(last)
        except (ValueError, TypeError):
            return True
        interval = max(int(_state.get("interval_minutes", 30) or 30), 1)
        return datetime.now() - last_dt >= timedelta(minutes=interval)

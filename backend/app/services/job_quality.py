# -*- coding: utf-8 -*-
"""岗位数据质量治理（方案③）：
- 岗位名归一：高级产品经理/资深算法工程师 → 产品经理/算法（保留内置岗位原名，避免重复种子）
- 技能规范化：java → Java、golang → Go 等别名归一
- 技能补全：技能稀疏的真实岗位（如 Java 岗只有 [java]）补齐为岗位标准技能集，
  从而让题库标签驱动召回（position_scope / select_candidates）命中更精准
- 存量数据清洗：reprocess_jobs 对库内真实岗位执行一次幂等清洗

说明：不改动 position_id，收藏/投递/面试关联不受影响。
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.position import Position
from app.services.job_crawler import JobItem
from app.services.position_directions import normalize_position_name
from app.services.skill_catalog import canonical_key, canonicalize_skill, complete_skills


def _dedup_skills(skills: list[str]) -> list[str]:
    """按规范化键去重，保留首次出现的顺序。"""
    seen: set[str] = set()
    out: list[str] = []
    for s in skills:
        k = canonical_key(s)
        if k and k not in seen:
            seen.add(k)
            out.append(str(s).strip())
    return out


def clean_job_item(item: JobItem) -> JobItem:
    """同步入库前的数据清洗（幂等）。

    - 非内置岗位：岗位名归一到方向键（内置岗位名保持原样，保证按名去重/种子稳定）
    - 技能：同义词规范化 + 去重 + 稀疏补全
    """
    if item.source != "builtin":
        norm = normalize_position_name(item.name)
        if norm:
            item.name = norm
    cleaned = _dedup_skills([canonicalize_skill(s) for s in (item.skills or [])])
    item.skills = complete_skills(item.name, item.direction, cleaned)
    return item


def reprocess_jobs(db: Session) -> dict:
    """对库内存量真实岗位执行一次清洗（幂等，跳过内置岗位）。

    返回统计：{"reprocessed": 扫描数, "changed": 实际改动数}
    """
    rows = db.scalars(
        select(Position).where(Position.source != "builtin", Position.status == "active")
    ).all()
    changed = 0
    for p in rows:
        before = (p.name, list(p.skills or []))
        norm = normalize_position_name(p.name)
        if norm:
            p.name = norm
        cleaned = _dedup_skills([canonicalize_skill(s) for s in (p.skills or [])])
        p.skills = complete_skills(p.name, p.direction, cleaned)
        if (p.name, list(p.skills)) != before:
            changed += 1
    db.commit()
    return {"reprocessed": len(rows), "changed": changed}

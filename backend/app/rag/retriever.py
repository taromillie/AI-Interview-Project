"""MVP 阶段的问题检索器（规则检索）。

从已发布的题库（KnowledgeAtom）中挑选候选问题：
1. 排除已问过的题目；
2. 按"题目/标签中的技能词是否命中最新回答"加权排序，优先追问相关内容；
3. 未命中时按难度从易到难兜底，保证永远有候选。

后续可无缝替换为向量检索（架构设计中预留 ChromaDB 接口）。
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.position import KnowledgeAtom


def _hit_score(atom: KnowledgeAtom, answer_text: str) -> int:
    """计算题目与回答的关键词命中分。"""
    answer = answer_text or ""
    pool = [atom.question, *atom.reference_points, *atom.tags]
    hits = 0
    for token in atom.tags:
        if token and token.lower() in answer.lower():
            hits += 2
    for token in atom.question:
        if token.strip() and len(token.strip()) >= 2 and token in answer:
            hits += 1
    return hits


def select_candidates(
    db: Session,
    position_id: int | None,
    asked_ids: set[int],
    answer_text: str | None = None,
    top_n: int = 6,
) -> list[KnowledgeAtom]:
    """返回推荐的候选题目列表（已过滤未问过 + published）。"""
    stmt = select(KnowledgeAtom).where(KnowledgeAtom.status == "published")
    if position_id:
        stmt = stmt.where(KnowledgeAtom.position_id == position_id)
    atoms = db.scalars(stmt).all()

    unasked = [a for a in atoms if a.id not in asked_ids]
    if not unasked:
        return []

    scored = sorted(
        unasked,
        key=lambda a: (_hit_score(a, answer_text), _diff_weight(a.difficulty)),
        reverse=True,
    )
    return scored[:top_n]


def _diff_weight(difficulty: str) -> int:
    """难度权重：junior>mid>senior（先易后难）。"""
    return {"junior": 3, "mid": 2, "senior": 1}.get(difficulty, 0)

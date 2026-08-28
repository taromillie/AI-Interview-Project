"""问题检索器（设计 AD-04，工作包 A）。

候选题目检索采用"向量召回优先 + 关键词降级"策略：
1. Embedding/向量库可用 → 向量召回（相似度优先），关键词结果补齐，保证召回不劣化；
2. Embedding 未配置或调用失败 → 无缝降级为关键词检索，绝不阻断主流程；
3. 已问题目与 draft/archived 原子始终被过滤。

关键词检索规则：
- 排除已问过的题目；
- 按"题目/标签中的技能词是否命中最新回答"加权排序，优先追问相关内容；
- 未命中时按难度从易到难兜底，保证永远有候选。
"""
import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.position import KnowledgeAtom
from app.rag.embedding import EmbeddingProvider
from app.rag.vector_store import query_top as _vector_query_top

logger = logging.getLogger(__name__)


def hit_score(atom: KnowledgeAtom, answer_text: str) -> int:
    """计算题目与回答的关键词命中分（供信号决策与测试使用）。"""
    answer = answer_text or ""
    hits = 0
    for token in atom.tags:
        if token and token.lower() in answer.lower():
            hits += 2
    for token in atom.question:
        if token.strip() and len(token.strip()) >= 2 and token in answer:
            hits += 1
    return hits


# 兼容旧引用（历史内部命名）
_hit_score = hit_score


def select_candidates(
    db: Session,
    position_id: int | None,
    asked_ids: set[int],
    answer_text: str | None = None,
    top_n: int = 6,
) -> list[KnowledgeAtom]:
    """关键词检索：返回推荐的候选题目列表（已过滤未问过 + published）。"""
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


async def aselect_candidates(
    db: Session,
    position_id: int | None,
    asked_ids: set[int],
    answer_text: str | None = None,
    top_n: int = 6,
    embedder: EmbeddingProvider | None = None,
) -> list[KnowledgeAtom]:
    """异步候选检索：向量召回优先，失败/不可用时降级为关键词检索。"""
    if embedder is not None:
        try:
            vec = await asyncio.to_thread(
                _vector_query_top,
                embedder,
                db,
                position_id=position_id,
                asked_ids=asked_ids,
                query_text=answer_text or "",
                top_n=top_n,
            )
            kw = select_candidates(db, position_id, asked_ids, answer_text, top_n)
            return _merge(vec, kw, top_n)
        except Exception as exc:  # noqa: BLE001 - 必须兜底，绝不阻断主流程
            logger.warning("向量检索失败，降级为关键词检索: %s", exc)
    return select_candidates(db, position_id, asked_ids, answer_text, top_n)


def _merge(
    vec_candidates: list[KnowledgeAtom],
    kw_candidates: list[KnowledgeAtom],
    top_n: int,
) -> list[KnowledgeAtom]:
    """向量结果优先 + 关键词结果补齐去重，保证召回不劣化。"""
    seen: set[int] = set()
    merged: list[KnowledgeAtom] = []
    for atom in [*vec_candidates, *kw_candidates]:
        if atom.id not in seen:
            seen.add(atom.id)
            merged.append(atom)
        if len(merged) >= top_n:
            break
    return merged


def _diff_weight(difficulty: str) -> int:
    """难度权重：junior>mid>senior（先易后难）。"""
    return {"junior": 3, "mid": 2, "senior": 1}.get(difficulty, 0)

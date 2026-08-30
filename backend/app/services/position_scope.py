"""岗位候选题范围（直属题 ∪ 岗位技能标签命中的题）。

背景：此前面试检索链路只按「岗位直属题」召回（select_candidates / query_top 均
按 position_id 精确过滤）。skills 稀疏的真实岗位（如爬虫岗位可能只有 1~2 条直属
题）容易题库耗尽、提前结束面试；而其他岗位下 tags 命中的同类题无法复用。

本模块把「岗位候选题范围」统一为：

    直属 published 原子 ∪ tags 命中岗位 skills 的 published 原子

与题库管理页的标签驱动筛选（question.py list_atoms）语义一致，
供关键词检索（retriever）与向量检索（vector_store）两条链路复用，
实现「不同岗位方向 → 面试考不同方向的题」。
"""
from sqlalchemy import String, func, or_, select
from sqlalchemy.orm import Session

from app.models.position import KnowledgeAtom, Position


def position_scope(
    db: Session, position_id: int
) -> tuple[set[int], set[int]] | None:
    """返回岗位的 (直属原子 id 集, 候选题 id 集 = 直属 ∪ 技能命中)。

    - 岗位不存在 → None（调用方退化为原「直属过滤」语义，保证行为一致）；
    - 岗位存在但无任何候选 → (空集, 空集)。
    """
    position = db.get(Position, position_id)
    if position is None:
        return None

    direct = set(
        db.scalars(
            select(KnowledgeAtom.id).where(
                KnowledgeAtom.status == "published",
                KnowledgeAtom.position_id == position_id,
            )
        ).all()
    )
    # tags 为 JSON 数组存储，按字符串包含匹配（与 list_atoms 一致）
    skills = [str(s).strip() for s in (position.skills or []) if str(s).strip()]
    if not skills:
        return direct, direct

    like_conds = [
        func.cast(KnowledgeAtom.tags, String).like(f'%"{skill}"%')
        for skill in skills
    ]
    hits = set(
        db.scalars(
            select(KnowledgeAtom.id).where(
                KnowledgeAtom.status == "published",
                KnowledgeAtom.position_id != position_id,
                or_(*like_conds),
            )
        ).all()
    )
    return direct, direct | hits

"""ChromaDB 向量存储封装（设计 AD-04 / NFR-07，工作包 A）。

原则：
- 向量索引是"可选增强"，可随时重建：以"当前 published 知识原子"为唯一事实来源，
  sync_published() 做差量同步（新增/更新/清理失效）；
- 任何异常向上抛出，由 retriever 捕获后降级为关键词检索，绝不阻断主流程；
- collection 名称随 embedding 模型变化，避免切换模型时维度冲突。
"""
import logging
import re

import chromadb
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.position import KnowledgeAtom
from app.rag.embedding import EmbeddingProvider
from app.services.position_scope import position_scope

logger = logging.getLogger(__name__)

ID_PREFIX = "atom:"


def _safe_collection_name(model: str) -> str:
    """将模型名 sanitize 进 collection 名，避免维度冲突。"""
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", model or "embedding").strip("_") or "embedding"
    return f"{settings.VECTOR_COLLECTION}_{name}"[:63]


def _client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)


def get_collection(embedder_name: str = "embedding"):
    return _client().get_or_create_collection(
        name=_safe_collection_name(embedder_name),
        metadata={"hnsw:space": "cosine"},
    )


def _atom_id(atom_id: int) -> str:
    return f"{ID_PREFIX}{atom_id}"


def sync_published(db: Session, embedder: EmbeddingProvider) -> int:
    """将 published 知识原子差量同步到向量集合，返回本次新增/更新条数。"""
    atoms = db.scalars(
        select(KnowledgeAtom).where(KnowledgeAtom.status == "published")
    ).all()
    collection = get_collection(embedder.name)

    existing_ids = set(collection.get()["ids"])
    wanted_ids = {_atom_id(a.id) for a in atoms}
    stale = existing_ids - wanted_ids
    if stale:
        collection.delete(ids=list(stale))
        logger.info("向量索引清理失效原子 %d 条", len(stale))

    new_atoms = [a for a in atoms if _atom_id(a.id) not in existing_ids]
    if not new_atoms:
        return 0

    vectors = embedder.embed([a.question for a in new_atoms])
    valid = [(a, v) for a, v in zip(new_atoms, vectors) if v]
    if not valid:
        return 0
    collection.upsert(
        ids=[_atom_id(a.id) for a, _ in valid],
        embeddings=[v for _, v in valid],
        documents=[a.question for a, _ in valid],
        metadatas=[
            {
                "position_id": a.position_id or 0,
                "status": a.status,
                "difficulty": a.difficulty,
                "tags": ",".join(a.tags or []),
            }
            for a, _ in valid
        ],
    )
    logger.info("向量索引新增/更新原子 %d 条", len(valid))
    return len(valid)


def query_top(
    embedder: EmbeddingProvider,
    db: Session,
    *,
    position_id: int | None,
    asked_ids: set[int],
    query_text: str,
    top_n: int,
) -> list[KnowledgeAtom]:
    """向量召回候选题目（已过滤未问过 + published），按相似度降序。

    岗位过滤不在向量层精确执行（skills 稀疏的岗位按 position_id 精确过滤会召回
    不足），改为召回后按「直属 ∪ 技能命中」范围（services/position_scope）在
    Python 端过滤，与关键词链路 select_candidates 语义一致。
    """
    sync_published(db, embedder)

    vectors = embedder.embed([query_text or ""])
    if not vectors:
        return []

    collection = get_collection(embedder.name)

    scope_ids: set[int] | None = None
    if position_id:
        scope = position_scope(db, position_id)
        if scope is None or not scope[1]:
            # 岗位不存在或无任何候选题 → 与原 position_id 精确过滤一致：无候选
            return []
        scope_ids = scope[1]

    result = collection.query(
        query_embeddings=[vectors[0]],
        n_results=max(top_n * 4, 24),  # 放宽岗位过滤后放大召回，保证过滤后仍有足够候选
        where={"status": "published"},
    )
    hit_ids = (result.get("ids") or [[]])[0] or []
    hit_ids = [i for i in hit_ids if i.startswith(ID_PREFIX)]
    if not hit_ids:
        return []

    numeric_ids = [int(i[len(ID_PREFIX):]) for i in hit_ids]
    atoms = {
        a.id: a
        for a in db.scalars(
            select(KnowledgeAtom).where(KnowledgeAtom.id.in_(numeric_ids))
        ).all()
    }
    candidates: list[KnowledgeAtom] = []
    for i in hit_ids:
        atom = atoms.get(int(i[len(ID_PREFIX):]))
        if atom is None or atom.id in asked_ids:
            continue
        if scope_ids is not None and atom.id not in scope_ids:
            continue
        candidates.append(atom)
        if len(candidates) >= top_n:
            break
    return candidates

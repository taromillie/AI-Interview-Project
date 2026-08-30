"""工作包 A 单元测试：四信号决策、有边界工具层、向量增强+关键词降级。

不依赖真实 LLM / Embedding / ChromaDB，全部使用纯函数或 fake 对象。
"""
import asyncio

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models.position import KnowledgeAtom, Position
from app.rag.next_question_decision import (
    DecisionSignals,
    analyze_signals,
    decide_strategy,
    is_low_information,
)
from app.rag.retriever import aselect_candidates, select_candidates
from app.agents.tools import ToolCallGuard, get_coverage


# ───────────────────────── 内存 DB 夹具 ─────────────────────────

@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()

    position = Position(
        id=1,
        name="后端开发工程师",
        direction="tech",
        difficulty="mid",
        skills=["Python", "MySQL", "Redis", "Docker"],
        is_public=True,
        status="active",
    )
    session.add(position)
    session.flush()

    atoms = [
        KnowledgeAtom(
            position_id=1,
            question="请解释 Python GIL 对多线程的影响？",
            reference_points=["GIL 与 CPU 密集/IO 密集"],
            tags=["Python", "GIL"],
            difficulty="junior",
            status="published",
        ),
        KnowledgeAtom(
            position_id=1,
            question="MySQL 索引失效的常见场景有哪些？",
            reference_points=["最左前缀"],
            tags=["MySQL", "索引"],
            difficulty="mid",
            status="published",
        ),
        KnowledgeAtom(
            position_id=1,
            question="Redis 缓存穿透如何解决？",
            reference_points=["布隆过滤器"],
            tags=["Redis", "缓存"],
            difficulty="mid",
            status="published",
        ),
        KnowledgeAtom(
            position_id=1,
            question="Docker 镜像与容器的关系？",
            reference_points=["分层"],
            tags=["Docker"],
            difficulty="junior",
            status="draft",  # 草稿应被过滤
        ),
        KnowledgeAtom(
            position_id=1,
            question="已问过的题目：MySQL 主从复制原理？",
            reference_points=["binlog"],
            tags=["MySQL"],
            difficulty="senior",
            status="published",
        ),
    ]
    session.add_all(atoms)
    session.commit()
    for a in atoms:
        session.refresh(a)
    yield session
    session.close()


# ───────────────────────── 四信号决策 ─────────────────────────

def test_is_low_information_short_answer():
    assert is_low_information("嗯") is True
    assert is_low_information("我平时会用 Python 写一些接口，然后接 MySQL。") is False


def test_analyze_signals_low_information():
    s = analyze_signals("不会", hit_score=0, probe_streak=0, avoid_streak=0)
    assert s.low_information is True
    assert s.weak_recall is False  # 低信息不算弱召回
    assert s.is_clear is True


def test_analyze_signals_weak_recall():
    # 有实质内容但候选命中为 0 → 偏题信号
    s = analyze_signals(
        "我负责过前端页面开发，用 Vue 写组件。", hit_score=0, probe_streak=0, avoid_streak=0
    )
    assert s.low_information is False
    assert s.weak_recall is True
    assert "偏题" in s.summary


def test_analyze_signals_avoid_streak():
    s = analyze_signals("不知道", hit_score=0, probe_streak=0, avoid_streak=2)
    assert s.avoid_streak == 2
    assert "连续 2 轮" in s.summary


def test_analyze_signals_exhausted_topic():
    s = analyze_signals("我知道一些基础用法。", hit_score=2, probe_streak=3, avoid_streak=0)
    assert s.exhausted_topic is True


def test_analyze_signals_project_hint():
    s = analyze_signals(
        "我之前做过订单系统，负责支付模块的开发和上线。", hit_score=2, probe_streak=0, avoid_streak=0
    )
    assert s.has_project_hint is True


def test_decide_strategy_priority_exhausted_first():
    """话题已尽必须换方向，优先级最高。"""
    s = DecisionSignals(low_information=True, exhausted_topic=True)
    assert decide_strategy(s, "hard") == "switch_topic"


def test_decide_strategy_weak_recall_remedy():
    s = DecisionSignals(weak_recall=True)
    assert decide_strategy(s, "normal") == "remedy"


def test_decide_strategy_avoid_streak_switch():
    s = DecisionSignals(avoid_streak=2)
    assert decide_strategy(s, "normal") == "switch_topic"


def test_decide_strategy_low_info_by_difficulty():
    """难度加权：hard 压测 deep_dive，easy 引导 remedy。"""
    assert decide_strategy(DecisionSignals(low_information=True), "hard") == "deep_dive"
    assert decide_strategy(DecisionSignals(low_information=True), "easy") == "remedy"
    assert decide_strategy(DecisionSignals(low_information=True), "normal") == "probe"


def test_decide_strategy_project_probe():
    s = DecisionSignals(has_project_hint=True)
    assert decide_strategy(s, "normal") == "project_probe"


def test_decide_strategy_no_signal():
    assert decide_strategy(DecisionSignals(), "normal") == "none"


# ───────────────────────── 有边界工具层 ─────────────────────────

def test_tool_guard_limits_calls():
    """单轮最多 3 次工具调用，超限拒绝。"""
    guard = ToolCallGuard(limit=3)
    assert guard.can_call("get_coverage") is True
    assert guard.can_call("get_coverage") is True
    assert guard.can_call("get_coverage") is True
    guard.record("get_coverage", True)
    guard.record("get_coverage", True)
    guard.record("get_coverage", True)
    assert guard.can_call("get_coverage") is False
    assert guard.used == 3
    assert "get_coverage" in guard.transcript


def test_coverage_computes():
    res = get_coverage(
        position_skills=["Python", "MySQL", "Redis", "Docker"],
        asked_questions=["请解释 Python GIL", "MySQL 索引失效"],
    )
    assert res.ok is True
    data = res.data
    assert "Python" in data["covered"]
    assert "MySQL" in data["covered"]
    assert "Redis" in data["uncovered"]
    assert data["ratio"] == 0.5
    assert "Redis" in data["hint"]


def test_get_resume_evidence_from_dict():
    from app.agents.tools import get_resume_evidence

    resume = {"skills": ["Python", "FastAPI"], "projects": ["订单系统 高并发"]}
    res = get_resume_evidence(resume)
    assert res.ok is True
    assert "Python" in res.data
    assert "订单系统" in res.data


# ───────────────────────── 检索器：过滤与降级 ─────────────────────────

def test_select_candidates_filters_draft_and_asked(db):
    """关键词检索：过滤 draft + 已问（无跨岗位题时仅剩直属 published 未问）。"""
    asked = {5}  # 已问过 id=5
    res = select_candidates(db, 1, asked, answer_text="我想问 MySQL 相关的", top_n=10)
    ids = {a.id for a in res}
    assert 4 not in ids          # draft 被过滤
    assert 5 not in ids          # 已问被过滤
    assert ids == {1, 2, 3}      # 仅剩 published 且未问的


def test_select_candidates_weights_by_answer(db):
    """回答命中话题应优先召回。"""
    res = select_candidates(db, 1, set(), answer_text="索引失效和优化", top_n=10)
    assert res[0].question.startswith("MySQL 索引失效")  # 命中排序靠前


def test_aselect_candidates_fallback_without_embedder(db):
    """无 Embedding 配置 → 直接走关键词检索，主流程不依赖向量。"""
    res = asyncio.run(
        aselect_candidates(db, 1, set(), answer_text="缓存穿透", top_n=3, embedder=None)
    )
    assert len(res) >= 1
    assert res[0].question.startswith("Redis 缓存穿透")


def test_aselect_candidates_vector_failure_fallback(db, monkeypatch):
    """向量检索失败 → 自动降级关键词，不抛异常。"""

    def _boom(*args, **kwargs):
        raise RuntimeError("vector store unavailable")

    monkeypatch.setattr("app.rag.retriever._vector_query_top", _boom)

    class FakeEmbedder:
        name = "fake-model"

        def embed(self, texts):
            raise AssertionError("不应走到 embed")

    res = asyncio.run(
        aselect_candidates(db, 1, set(), answer_text="MySQL", top_n=3, embedder=FakeEmbedder())
    )
    assert len(res) >= 1
    assert res[0].question.startswith("MySQL 索引失效")


# ───────────────────── 岗位候选题范围（直属 ∪ 技能命中） ─────────────────────

def test_select_candidates_includes_skill_hits_from_other_position(db):
    """技能标签命中的其他岗位题可被召回，且直属题排在前面（修复检索断裂）。"""
    other = Position(
        id=2, name="MySQL 工程师", direction="tech", difficulty="mid",
        skills=["MySQL"], is_public=True, status="active",
    )
    db.add(other)
    db.flush()
    db.add(KnowledgeAtom(
        position_id=2,
        question="MySQL 事务隔离级别有哪些？",
        reference_points=["脏读", "不可重复读", "幻读"],
        tags=["MySQL", "事务"],
        difficulty="mid",
        status="published",
    ))
    db.commit()

    res = select_candidates(db, 1, set(), top_n=10)
    questions = [a.question for a in res]
    hit_idx = next(i for i, q in enumerate(questions) if "事务隔离级别" in q)
    direct_idx = questions.index("请解释 Python GIL 对多线程的影响？")
    assert hit_idx > direct_idx        # 直属题（GIL）排在技能命中题之前
    assert 4 not in {a.id for a in res}  # 草稿仍被过滤


def test_select_candidates_empty_skills_falls_back_to_direct(db):
    """岗位 skills 为空 → 仅直属题（不因放宽范围而召回全部题库）。"""
    other = Position(
        id=2, name="冷门岗位", direction="tech", difficulty="mid",
        skills=[], is_public=True, status="active",
    )
    db.add(other)
    db.flush()
    db.add(KnowledgeAtom(
        position_id=2,
        question="该冷门岗位专属题",
        reference_points=["无"],
        tags=["冷门"],
        difficulty="mid",
        status="published",
    ))
    db.commit()

    res = select_candidates(db, 2, set(), top_n=10)
    assert [a.question for a in res] == ["该冷门岗位专属题"]


def test_query_top_filters_by_position_scope(db, monkeypatch):
    """向量召回后按岗位范围（直属 ∪ 技能命中）过滤：草稿/无关题不进候选。"""
    from app.rag import vector_store

    other = Position(
        id=2, name="MySQL 工程师", direction="tech", difficulty="mid",
        skills=["MySQL"], is_public=True, status="active",
    )
    db.add(other)
    db.flush()
    other_atom = KnowledgeAtom(
        position_id=2,
        question="MySQL 事务隔离级别有哪些？",
        reference_points=["脏读", "不可重复读", "幻读"],
        tags=["MySQL", "事务"],
        difficulty="mid",
        status="published",
    )
    db.add(other_atom)
    db.commit()

    class FakeEmbedder:
        name = "fake-model"

        def embed(self, texts):
            return [[0.1] * 4] * len(texts)

    class FakeCollection:
        def query(self, query_embeddings, n_results, where):
            # 模拟 Chroma 返回全部 published 原子
            ids = [
                f"atom:{a.id}"
                for a in db.scalars(
                    select(KnowledgeAtom).where(KnowledgeAtom.status == "published")
                ).all()
            ]
            return {"ids": [ids]}

    monkeypatch.setattr(vector_store, "get_collection", lambda name: FakeCollection())
    monkeypatch.setattr(vector_store, "sync_published", lambda db, emb: 0)

    res = vector_store.query_top(
        FakeEmbedder(), db,
        position_id=1, asked_ids=set(), query_text="MySQL", top_n=10,
    )
    ids = {a.id for a in res}
    assert 4 not in ids                       # 草稿被过滤
    assert other_atom.id in ids               # 技能命中的其他岗位题被召回
    assert ids <= {1, 2, 3, 5, other_atom.id}  # 全部落在岗位候选题范围内

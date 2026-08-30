# -*- coding: utf-8 -*-
"""面试编排器测试：状态机流转、LLM 失败兜底、探针限制与 finish 幂等。"""
import json

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.agents.prompts import HR_QUESTION_BANK, SALARY_QUESTION_BANK, SWITCH_QUESTION_BANK
from app.core.db import Base
from app.core.exceptions import AppError
from app.llm.base import LLMProvider
from app.models.interview import Interview, InterviewMessage, Report
from app.models.interviewer import Interviewer
from app.models.position import KnowledgeAtom, Position
from app.models.user import User
from app.services.interview_orchestrator import (
    MAX_PROBE_STREAK,
    REPORT_PENDING_SUMMARY,
    InterviewOrchestrator,
)


class FakeLLM(LLMProvider):
    """可配置 LLM：默认返回 ask_question；fail=True 时抛异常。"""

    def __init__(self, decision=None, fail: bool = False):
        self._decision = decision
        self._fail = fail

    @property
    def name(self) -> str:
        return "fake"

    async def achat(self, messages, *, temperature=0.3, max_tokens=2048) -> str:
        if self._fail:
            raise RuntimeError("LLM 模拟失败")
        decision = self._decision or {
            "action": "ask_question",
            "strategy": "probe",
            "question": "再详细讲讲这部分？",
            "reason": "test",
        }
        return json.dumps(decision, ensure_ascii=False)

    def stream(self, messages, *, temperature=0.7, max_tokens=2048):
        raise NotImplementedError


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    yield session
    session.close()


@pytest.fixture()
def user(db):
    u = User(username="alice", password_hash="x", email="a@example.com")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture()
def position(db):
    p = Position(name="Python 后端开发", skills=["Python", "Django"])
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def make_interview(db, user, position, *, max_rounds=6, status="created", interview_type="normal", interviewer_id=None):
    it = Interview(
        user_id=user.id,
        position_id=position.id,
        difficulty="normal",
        max_rounds=max_rounds,
        status=status,
        interview_type=interview_type,
        interviewer_id=interviewer_id,
        config={},
    )
    db.add(it)
    db.commit()
    db.refresh(it)
    return it


def make_interviewer(db, *, name, interview_type="normal"):
    iv = Interviewer(
        name=name,
        title="测试角色",
        persona="测试人设",
        style="专业严谨",
        interview_type=interview_type,
    )
    db.add(iv)
    db.commit()
    db.refresh(iv)
    return iv


def make_atom(db, position, *, question="讲讲 Python 的 GIL？", tags=None):
    atom = KnowledgeAtom(
        position_id=position.id,
        question=question,
        tags=tags or ["Python"],
        difficulty="mid",
        status="published",
    )
    db.add(atom)
    db.commit()
    db.refresh(atom)
    return atom


def messages_of(db, interview_id):
    return list(
        db.scalars(
            select(InterviewMessage)
            .where(InterviewMessage.interview_id == interview_id)
            .order_by(InterviewMessage.id)
        )
    )


# ── start：开场 ──
class TestStart:
    async def test_start_creates_opening(self, db, user, position):
        it = make_interview(db, user, position)
        orch = InterviewOrchestrator(db, user, it, FakeLLM())
        outcome = await orch.start()
        assert outcome["event"] == "question"
        assert outcome["data"]["strategy"] == "opening"
        assert it.status == "asking"
        msgs = messages_of(db, it.id)
        assert len(msgs) == 1
        assert msgs[0].role == "assistant"
        assert msgs[0].strategy == "opening"

    async def test_start_idempotent(self, db, user, position):
        it = make_interview(db, user, position)
        orch = InterviewOrchestrator(db, user, it, FakeLLM())
        await orch.start()
        await orch.start()
        assert len(messages_of(db, it.id)) == 1  # 不重复保存开场

    async def test_start_rejected_after_reported(self, db, user, position):
        it = make_interview(db, user, position, status="reported")
        orch = InterviewOrchestrator(db, user, it, FakeLLM())
        with pytest.raises(AppError):
            await orch.start()


# ── answer：出题与兜底 ──
class TestAnswer:
    async def test_answer_returns_next_question(self, db, user, position):
        make_atom(db, position)
        it = make_interview(db, user, position, max_rounds=3)
        orch = InterviewOrchestrator(db, user, it, FakeLLM())
        await orch.start()
        outcome = await orch.answer("我之前做过高并发场景，用 Redis 做缓存。")
        assert outcome["event"] == "question"
        assert outcome["data"]["round"] == 2
        roles = [m.role for m in messages_of(db, it.id)]
        assert roles == ["assistant", "user", "assistant"]

    async def test_max_rounds_reached_finishes(self, db, user, position):
        make_atom(db, position)
        it = make_interview(db, user, position, max_rounds=1)
        orch = InterviewOrchestrator(db, user, it, FakeLLM())
        await orch.start()
        outcome = await orch.answer("我的回答")
        assert outcome["event"] == "finished"
        assert it.status == "reported"
        report = db.scalars(select(Report).where(Report.interview_id == it.id)).one()
        assert report.summary == REPORT_PENDING_SUMMARY

    async def test_llm_failure_falls_back_to_candidate(self, db, user, position):
        atom = make_atom(db, position, question="讲讲 HTTP 缓存机制？")
        it = make_interview(db, user, position, max_rounds=3)
        orch = InterviewOrchestrator(db, user, it, FakeLLM(fail=True))
        await orch.start()
        outcome = await orch.answer("这个我不太熟悉。")
        assert outcome["event"] == "question"
        # LLM 失败后规则回退，从候选题库中出题
        assert outcome["data"]["question"] == atom.question

    async def test_probe_streak_forced_switch_topic(self, db, user, position):
        make_atom(db, position)
        it = make_interview(db, user, position, max_rounds=10)
        llm = FakeLLM(
            {
                "action": "ask_question",
                "strategy": "probe",
                "question": "再详细讲讲？",
                "reason": "test",
            }
        )
        orch = InterviewOrchestrator(db, user, it, llm)
        await orch.start()
        for _ in range(MAX_PROBE_STREAK):
            await orch.answer("好的，继续。")
        outcome = await orch.answer("好的，继续。")
        # 连续追问达到上限，必须强制切换话题
        assert outcome["data"]["strategy"] == "switch_topic"


# ── finish：结束与幂等 ──
class TestFinish:
    async def test_finish_creates_placeholder_report(self, db, user, position):
        it = make_interview(db, user, position)
        orch = InterviewOrchestrator(db, user, it, FakeLLM())
        outcome = await orch.finish()
        assert outcome["event"] == "finished"
        assert "report_id" in outcome["data"]
        assert it.status == "reported"
        report = db.get(Report, outcome["data"]["report_id"])
        assert report is not None
        assert report.summary == REPORT_PENDING_SUMMARY
        strategies = [m.strategy for m in messages_of(db, it.id)]
        assert "farewell" in strategies

    async def test_finish_idempotent(self, db, user, position):
        it = make_interview(db, user, position)
        orch = InterviewOrchestrator(db, user, it, FakeLLM())
        await orch.finish()
        with pytest.raises(AppError):
            await orch.finish()

    async def test_finish_rejected_when_reported(self, db, user, position):
        it = make_interview(db, user, position, status="reported")
        orch = InterviewOrchestrator(db, user, it, FakeLLM())
        with pytest.raises(AppError):
            await orch.finish()


# ── 谈薪模式（v1.2：interview_type=salary） ──
class TestSalaryMode:
    async def test_salary_opening_is_salary_related(self, db, user, position):
        it = make_interview(db, user, position, interview_type="salary")
        orch = InterviewOrchestrator(db, user, it, FakeLLM())
        outcome = await orch.start()
        q = outcome["data"]["question"]
        assert "薪资" in q or "谈薪" in q

    async def test_salary_fallback_uses_salary_bank(self, db, user, position):
        # 谈薪模式不依赖技术题库：LLM 失败时从内置谈薪问题库出题
        it = make_interview(db, user, position, interview_type="salary")
        orch = InterviewOrchestrator(db, user, it, FakeLLM(fail=True))
        await orch.start()
        outcome = await orch.answer("我之前做过三年后端开发。")
        assert outcome["event"] == "question"
        assert outcome["data"]["question"] in SALARY_QUESTION_BANK

    async def test_salary_ignores_tech_question_bank(self, db, user, position):
        # 即使题库里有技术原子，谈薪模式也不应把它当作候选问题
        make_atom(db, position, question="讲讲 Python 的 GIL？")
        it = make_interview(db, user, position, interview_type="salary")
        orch = InterviewOrchestrator(db, user, it, FakeLLM(fail=True))
        await orch.start()
        outcome = await orch.answer("我主要是写后端接口。")
        assert outcome["event"] == "question"
        assert outcome["data"]["question"] in SALARY_QUESTION_BANK
        assert outcome["data"]["question"] != "讲讲 Python 的 GIL？"

    async def test_salary_project_probe_normalized(self, db, user, position):
        # 谈薪模式无"项目追问"概念，LLM 输出的 project_probe 归一为普通追问
        it = make_interview(db, user, position, interview_type="salary")
        llm = FakeLLM(
            {
                "action": "ask_question",
                "strategy": "project_probe",
                "question": "讲讲你那个项目？",
                "reason": "test",
            }
        )
        orch = InterviewOrchestrator(db, user, it, llm)
        await orch.start()
        outcome = await orch.answer("我之前负责过一个电商平台项目。")
        assert outcome["data"]["strategy"] == "probe"


# ── 面试官专属模式（v1.3：interviewer.name 命中专属配置） ──
class TestInterviewerMode:
    async def test_cto_interviewer_uses_knowledge_bank(self, db, user, position):
        # CTO 技术面仍走技术题库检索，但决策提示词是架构视角
        make_atom(db, position, question="讲讲 Python 的 GIL？")
        iv = make_interviewer(db, name="CTO 技术面")
        it = make_interview(db, user, position, interviewer_id=iv.id, max_rounds=3)
        orch = InterviewOrchestrator(db, user, it, FakeLLM(fail=True))
        await orch.start()
        outcome = await orch.answer("我做过订单系统，用 MySQL 和 Redis 缓存。")
        assert outcome["event"] == "question"
        assert outcome["data"]["question"] == "讲讲 Python 的 GIL？"  # 技术题库出题

    async def test_hr_interviewer_uses_hr_bank(self, db, user, position):
        # HR 综合面用内置行为面问题库，不检索技术题库
        make_atom(db, position, question="讲讲 Python 的 GIL？")
        iv = make_interviewer(db, name="HR 综合面")
        it = make_interview(db, user, position, interviewer_id=iv.id, max_rounds=3)
        orch = InterviewOrchestrator(db, user, it, FakeLLM(fail=True))
        await orch.start()
        outcome = await orch.answer("我做过三年后端开发。")
        assert outcome["event"] == "question"
        assert outcome["data"]["question"] in HR_QUESTION_BANK
        assert outcome["data"]["question"] != "讲讲 Python 的 GIL？"

    async def test_switch_interviewer_uses_switch_bank(self, db, user, position):
        # 转行面试官用内置转行问题库
        make_atom(db, position, question="讲讲 Python 的 GIL？")
        iv = make_interviewer(db, name="转行质疑面试官")
        it = make_interview(db, user, position, interviewer_id=iv.id, max_rounds=3)
        orch = InterviewOrchestrator(db, user, it, FakeLLM(fail=True))
        await orch.start()
        outcome = await orch.answer("我以前做运营，想转开发。")
        assert outcome["event"] == "question"
        assert outcome["data"]["question"] in SWITCH_QUESTION_BANK
        assert outcome["data"]["question"] != "讲讲 Python 的 GIL？"

    async def test_pressure_interviewer_uses_knowledge_bank(self, db, user, position):
        # 压力面继续用技术题库，但决策提示词不同
        make_atom(db, position, question="讲讲 Python 的 GIL？")
        iv = make_interviewer(db, name="压力面")
        it = make_interview(db, user, position, interviewer_id=iv.id, max_rounds=3)
        orch = InterviewOrchestrator(db, user, it, FakeLLM(fail=True))
        await orch.start()
        outcome = await orch.answer("我做过一个秒杀系统。")
        assert outcome["data"]["question"] == "讲讲 Python 的 GIL？"

    async def test_custom_interviewer_falls_back_by_type(self, db, user, position):
        # 用户自建面试官不在映射表 → 按 interview_type 回退（salary → 谈薪库）
        iv = make_interviewer(db, name="我的自定义面试官", interview_type="salary")
        it = make_interview(db, user, position, interviewer_id=iv.id, max_rounds=3, interview_type="salary")
        orch = InterviewOrchestrator(db, user, it, FakeLLM(fail=True))
        await orch.start()
        outcome = await orch.answer("我期望薪资 25k。")
        assert outcome["event"] == "question"
        assert outcome["data"]["question"] in SALARY_QUESTION_BANK

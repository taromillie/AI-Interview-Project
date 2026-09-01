# -*- coding: utf-8 -*-
"""核心 service 兜底测试：LLM 失败时必须走规则回退，接口总能返回合理结果。"""
from typing import AsyncIterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.llm.base import LLMProvider
from app.models.career import AbilityProfile, SalaryEval
from app.models.resume import MatchDiagnostic, Resume
from app.models.study import StudyPlan
from app.schemas.career import SalaryEvalRequest
from app.services.resume_matcher import run_diagnostic
from app.services.salary_eval import run_salary_eval
from app.services.study_plan import generate_study_plan


class FailingLLM(LLMProvider):
    """总是抛异常的 LLM：用于验证各服务规则兜底。"""

    async def achat(self, messages, *, temperature=0.3, max_tokens=2048) -> str:
        raise RuntimeError("simulated LLM outage")

    def stream(self, messages, *, temperature=0.7, max_tokens=2048) -> AsyncIterator[str]:
        async def gen():
            raise RuntimeError("simulated LLM outage")
            yield ""  # pragma: no cover

        return gen()

    @property
    def name(self) -> str:
        return "failing"


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    yield session
    session.close()


@pytest.fixture()
def llm() -> FailingLLM:
    return FailingLLM()


def _resume(user_id: int = 1) -> Resume:
    return Resume(
        user_id=user_id,
        name="测试简历",
        raw_text="张三，3 年后端开发，熟悉 Python 与 FastAPI。",
        parsed_json={"basic": {"name": "张三", "years_of_exp": "3年"}},
        skills=["Python", "FastAPI"],
    )


async def test_resume_matcher_falls_back_to_rules(db, llm):
    """JD 技能提取与建议生成全部失败 → 规则兜底：score 0、规则建议、正常落库。"""
    resume = _resume()
    db.add(resume)
    db.commit()
    db.refresh(resume)

    diag = await run_diagnostic(db, llm, resume, "JD 要求：熟悉 Python，具备后端开发经验。")
    db.refresh(diag)

    assert isinstance(diag, MatchDiagnostic)
    assert diag.id is not None
    assert diag.match_score == 0.0  # LLM 提取失败 → 无必需技能，分数为 0
    assert diag.gaps == []
    assert diag.suggestions == ["补充更多量化成果（数据、指标），增强说服力"]


async def test_salary_eval_falls_back_to_rule_table(db, llm):
    """LLM 失败 → 城市×年限×岗位基数规则表：区间合理、策略非空。"""
    payload = SalaryEvalRequest(
        skill_stack=["Python"],
        years=3,
        city="北京",
        target_position="后端开发",
    )
    resume = _resume()
    db.add(resume)
    db.commit()
    db.refresh(resume)

    ev = await run_salary_eval(db, llm, user_id=1, payload=payload, resume=resume)
    db.refresh(ev)

    assert isinstance(ev, SalaryEval)
    assert ev.id is not None
    lo, mid, hi = ev.result["salary_range"]
    # 北京 1.0 × 后端 22000 × (1+0.3) = 28600；区间 [22880, 28600, 37180]
    assert mid == 28600
    assert lo < mid < hi
    assert any("城市系数" in f for f in ev.result["factors"])
    assert len(ev.result["strategy"]) >= 3


async def test_study_plan_falls_back_to_rule_plan(db, llm):
    """LLM 失败 → 三阶段规则模板：任务天数完整、标题含目标岗位。"""
    resume = _resume()
    db.add(resume)
    db.commit()
    db.refresh(resume)

    plan = await generate_study_plan(
        db, llm, user_id=1, target_position="后端开发", days=10, resume=resume
    )
    db.refresh(plan)

    assert isinstance(plan, StudyPlan)
    assert plan.id is not None
    assert plan.days == 10
    assert len(plan.tasks) == 10
    assert {t["day"] for t in plan.tasks} == set(range(1, 11))
    assert "后端开发" in plan.title
    assert "三阶段" in plan.summary
    # 规则模板每个任务都有主题与描述
    assert all(t["topics"] and t["description"] for t in plan.tasks)


async def test_study_plan_uses_profile_gaps_in_fallback(db, llm):
    """画像缺口 <60 分的维度会并入规则兜底的学习主题。"""
    profile = AbilityProfile(
        user_id=1,
        dimensions={"系统设计": 45, "算法": 80},
        skill_scores={},
    )
    db.add(profile)
    db.commit()

    plan = await generate_study_plan(
        db, llm, user_id=1, target_position="后端开发", days=6, resume=None
    )
    db.refresh(plan)

    assert len(plan.tasks) == 6
    # 缺口维度应出现在兜底任务的主题/描述中
    all_topics = "".join("、".join(t["topics"]) for t in plan.tasks)
    assert "系统设计" in all_topics


async def test_study_plan_no_llm_uses_rule_plan(db):
    """未配置 LLM（llm=None）→ 同样走规则模板，不抛异常、正常落库。"""
    plan = await generate_study_plan(
        db, None, user_id=1, target_position="Java开发", days=7, resume=None
    )
    db.refresh(plan)

    assert isinstance(plan, StudyPlan)
    assert plan.id is not None
    assert plan.days == 7
    assert len(plan.tasks) == 7
    assert {t["day"] for t in plan.tasks} == set(range(1, 8))
    assert "Java开发" in plan.title
    assert all(t["topics"] and t["description"] for t in plan.tasks)

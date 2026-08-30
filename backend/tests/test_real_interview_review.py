# -*- coding: utf-8 -*-
"""真实面试复盘服务测试：JSON 解析、规则兜底、逐题批改写回。"""
import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.llm.base import LLMProvider, ChatMessage
from app.models.real_interview import RealInterview, RealInterviewItem
from app.services.real_interview_review import (
    _clamp,
    _extract_json,
    _rule_review,
    review_real_interview,
)


class FakeLLM(LLMProvider):
    def __init__(self, payload):
        self._payload = payload

    @property
    def name(self) -> str:
        return "fake"

    async def achat(self, messages, *, temperature=0.3, max_tokens=2048) -> str:
        if isinstance(self._payload, Exception):
            raise self._payload
        if callable(self._payload):
            return self._payload(messages, temperature=temperature, max_tokens=max_tokens)
        return json.dumps(self._payload, ensure_ascii=False)

    def stream(self, messages, *, temperature=0.7, max_tokens=2048):
        raise NotImplementedError


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    iv = RealInterview(
        user_id=1, company="字节跳动", position="后端开发", round_type="技术一面",
        interview_date="2026-08-20", notes="考察基础",
    )
    session.add(iv)
    session.flush()
    session.add_all([
        RealInterviewItem(
            interview_id=iv.id,
            question="什么是缓存穿透？如何解决？",
            answer="缓存穿透是查询不存在的数据直接打到数据库，用布隆过滤器拦截。",
        ),
        RealInterviewItem(
            interview_id=iv.id,
            question="MySQL 索引失效场景？",
            answer="对索引列做函数运算、隐式类型转换会导致失效。",
        ),
    ])
    session.commit()
    session.refresh(iv)
    yield session, iv
    session.close()


VALID_LLM_REVIEW = {
    "overall_score": 78,
    "dimensions": {"tech": 80, "expression": 70, "logic": 75, "project": 60},
    "item_reviews": [
        {"question": "什么是缓存穿透？如何解决？", "score": 85, "comment": "回答准确，可补充缓存空值场景。"},
        {"question": "MySQL 索引失效场景？", "score": 72, "comment": "回答正确，可补充最左前缀原则。"},
    ],
    "suggestions": ["多练习系统设计题"],
    "summary": "基础扎实，表达清晰",
}


# ── _extract_json ──
class TestExtractJson:
    def test_plain_json(self):
        assert _extract_json('{"a": 1}') == {"a": 1}

    def test_code_fenced_json(self):
        raw = '```json\n{"a": 1}\n```'
        assert _extract_json(raw) == {"a": 1}

    def test_missing_json_raises(self):
        with pytest.raises(Exception):
            _extract_json("没有 JSON")


# ── _clamp ──
class TestClamp:
    def test_bounds(self):
        assert _clamp(120) == 100.0
        assert _clamp(-5) == 0.0
        assert _clamp(66.6) == 66.6

    def test_invalid_fallback(self):
        assert _clamp("abc") == 50.0
        assert _clamp(None) == 50.0


# ── _rule_review ──
class TestRuleReview:
    def test_scores_and_structure(self, db):
        session, iv = db
        items = session.query(RealInterviewItem).filter_by(interview_id=iv.id).all()
        review = _rule_review(items)
        assert review["overall_score"] > 0
        assert len(review["item_reviews"]) == 2
        assert review["item_reviews"][0]["question"].startswith("什么是缓存穿透")
        assert review["dimensions"]["tech"] == 0
        assert review["suggestions"]

    def test_empty_items(self):
        review = _rule_review([])
        assert review["overall_score"] == 0.0
        assert review["item_reviews"] == []


# ── review_real_interview ──
class TestReviewRealInterview:
    async def test_llm_writes_back(self, db):
        session, iv = db
        review = await review_real_interview(session, FakeLLM(VALID_LLM_REVIEW), iv)
        assert review["overall_score"] == 78.0
        assert review["item_reviews"][0]["score"] == 85.0
        items = session.query(RealInterviewItem).order_by(RealInterviewItem.id).all()
        assert items[0].score == 85.0
        assert items[0].comment == "回答准确，可补充缓存空值场景。"
        # 写回 interview.review
        session.refresh(iv)
        assert iv.review["overall_score"] == 78.0

    async def test_llm_exception_falls_back(self, db):
        session, iv = db
        review = await review_real_interview(session, FakeLLM(RuntimeError("timeout")), iv)
        assert review["summary"].startswith("本次复盘由规则引擎生成")
        items = session.query(RealInterviewItem).order_by(RealInterviewItem.id).all()
        assert items[0].score > 0
        assert "已按回答完整度粗略评分" in items[0].comment

    async def test_llm_invalid_json_falls_back(self, db):
        session, iv = db
        review = await review_real_interview(session, FakeLLM("not json at all"), iv)
        assert review["summary"].startswith("本次复盘由规则引擎生成")

    async def test_empty_items_no_crash(self, db):
        session, iv = db
        session.query(RealInterviewItem).filter_by(interview_id=iv.id).delete()
        session.commit()
        # LLM 异常时规则兜底：无题目 → 0 分、空批改
        review = await review_real_interview(session, FakeLLM(RuntimeError("no items")), iv)
        assert review["overall_score"] == 0.0
        assert review["item_reviews"] == []
        # LLM 正常但题目为空 → 不逐题批改、不崩溃
        review2 = await review_real_interview(session, FakeLLM(VALID_LLM_REVIEW), iv)
        assert review2["item_reviews"] == []

# -*- coding: utf-8 -*-
"""复盘报告生成服务测试：LLM 成功/非法 JSON/规则降级。"""
import json

import pytest

from app.llm.base import LLMProvider
from app.models.interview import InterviewMessage
from app.services.feedback import _clamp, _extract_json, fallback_report, generate_report


class FakeLLM(LLMProvider):
    def __init__(self, payload):
        self._payload = payload

    @property
    def name(self) -> str:
        return "fake"

    async def achat(self, messages, *, temperature=0.3, max_tokens=2048) -> str:
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload

    def stream(self, messages, *, temperature=0.7, max_tokens=2048):
        raise NotImplementedError


def msg(role: str, content: str) -> InterviewMessage:
    return InterviewMessage(role=role, content=content, strategy=None, evidence_atom_ids=[])


def transcript_messages() -> list[InterviewMessage]:
    return [
        msg("assistant", "你好，请做自我介绍。"),
        msg("user", "我是 3 年后端工程师，负责过电商订单系统。"),
        msg("assistant", "讲讲 Redis 缓存穿透怎么处理？"),
        msg("user", "用布隆过滤器加缓存空值兜底。"),
    ]


VALID_PAYLOAD = {
    "overall_score": 82,
    "dimensions": {"tech": 85, "expression": 80, "logic": 78, "project": 86},
    "question_feedback": [
        {"question": "自我介绍", "answer": "3 年后端", "score": 80, "comment": "清晰"},
    ],
    "weak_points": ["缺少量化指标"],
    "coverage": {"covered": ["Redis"], "uncovered": ["MySQL 索引"]},
    "learning_path": [
        {"phase": "基础夯实", "action": "复习 MySQL", "duration": "1 周"},
    ],
    "summary": "整体表现良好，建议补充量化指标。",
}


def _json(payload) -> str:
    return json.dumps(payload, ensure_ascii=False)


# ── _extract_json ──
class TestExtractJson:
    def test_plain(self):
        assert _extract_json('{"a": 1}') == {"a": 1}

    def test_no_json_raises(self):
        with pytest.raises(ValueError):
            _extract_json("抱歉，我无法生成 JSON")

    def test_code_fenced(self):
        data = _extract_json('```json\n{"a": 1}\n```')
        assert data["a"] == 1


# ── _clamp ──
class TestClamp:
    def test_bounds(self):
        assert _clamp(-5) == 0.0
        assert _clamp(150) == 100.0

    def test_non_numeric_defaults(self):
        assert _clamp("abc") == 50.0
        assert _clamp(None) == 50.0

    def test_normal_value(self):
        assert _clamp(77) == 77.0


# ── generate_report ──
class TestGenerateReport:
    async def test_valid_payload_normalized(self):
        llm = FakeLLM(_json(VALID_PAYLOAD))
        data = await generate_report(
            llm=llm,
            position_name="后端",
            position_skills=["Redis", "MySQL"],
            resume_brief="",
            messages=transcript_messages(),
        )
        assert data["overall_score"] == 82.0
        assert data["dimensions"]["tech"] == 85.0
        assert data["question_feedback"][0]["score"] == 80.0
        assert data["learning_path"][0]["phase"] == "基础夯实"
        assert data["coverage"]["covered"] == ["Redis"]

    async def test_invalid_json_raises(self):
        llm = FakeLLM("这不是 JSON")
        with pytest.raises(ValueError):
            await generate_report(
                llm=llm,
                position_name="后端",
                position_skills=[],
                resume_brief="",
                messages=transcript_messages(),
            )

    async def test_out_of_range_scores_clamped(self):
        payload = dict(VALID_PAYLOAD)
        payload["overall_score"] = 999
        payload["dimensions"] = {"tech": -30, "expression": 55, "logic": 101, "project": 70}
        data = await generate_report(
            llm=FakeLLM(_json(payload)),
            position_name="后端",
            position_skills=[],
            resume_brief="",
            messages=transcript_messages(),
        )
        assert data["overall_score"] == 100.0
        assert data["dimensions"]["tech"] == 0.0
        assert data["dimensions"]["logic"] == 100.0

    async def test_empty_learning_path_falls_back_to_rule(self):
        payload = dict(VALID_PAYLOAD)
        payload["learning_path"] = []
        data = await generate_report(
            llm=FakeLLM(_json(payload)),
            position_name="后端",
            position_skills=["Redis"],
            resume_brief="",
            messages=transcript_messages(),
        )
        assert len(data["learning_path"]) >= 3  # 规则兜底路线


# ── fallback_report：规则降级 ──
class TestFallbackReport:
    def test_empty_messages_all_zero(self):
        data = fallback_report([])
        assert data["overall_score"] == 0.0
        assert data["dimensions"] == {"tech": 0, "expression": 0, "logic": 0, "project": 0}
        assert data["weak_points"] == ["面试未产生有效作答"]

    def test_with_messages_scores_in_range(self):
        data = fallback_report(transcript_messages())
        assert 0 <= data["overall_score"] <= 100
        for v in data["dimensions"].values():
            assert 0 <= v <= 100
        assert data["question_feedback"]
        assert data["learning_path"]  # 规则生成的学习路线

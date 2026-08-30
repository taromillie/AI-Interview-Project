# -*- coding: utf-8 -*-
"""面试官 Agent 测试：决策解析、规则回退、开场与四信号策略映射。"""
import json

import pytest

from app.agents.interview_agent import InterviewAgent, _extract_json
from app.llm.base import LLMProvider
from app.rag.next_question_decision import (
    DecisionSignals,
    analyze_signals,
    decide_strategy,
    is_low_information,
)


class FakeLLM(LLMProvider):
    def __init__(self, payload):
        self._payload = payload
        self.last_messages = None

    @property
    def name(self) -> str:
        return "fake"

    async def achat(self, messages, *, temperature=0.3, max_tokens=2048) -> str:
        self.last_messages = messages
        if isinstance(self._payload, Exception):
            raise self._payload
        if callable(self._payload):
            return self._payload(messages)
        return json.dumps(self._payload, ensure_ascii=False)

    def stream(self, messages, *, temperature=0.7, max_tokens=2048):
        raise NotImplementedError


@pytest.fixture()
def agent():
    return InterviewAgent(FakeLLM(None))


DECIDE_KWARGS = dict(
    position_name="Python 后端工程师",
    position_skills=["Python", "MySQL"],
    resume_brief="3 年后端经验",
    history_text="已提问 2 轮",
    latest_answer="项目中用 Redis 做了缓存",
    candidates=["什么是缓存穿透？", "如何保证幂等？"],
    asked_rounds=2,
    max_rounds=6,
)


# ── _extract_json ──
class TestExtractJson:
    def test_plain(self):
        assert _extract_json('{"action": "finish"}')["action"] == "finish"

    def test_code_fenced(self):
        raw = '```json\n{"action": "finish"}\n```'
        assert _extract_json(raw)["action"] == "finish"

    def test_with_surrounding_noise(self):
        raw = '好的，以下是决策：\n{"action": "finish"}\n希望有帮助！'
        assert _extract_json(raw)["action"] == "finish"


# ── decide_next ──
class TestDecideNext:
    async def test_valid_decision_used(self):
        llm = FakeLLM({"action": "ask_question", "strategy": "probe", "question": "追问细节？", "reason": "深入"})
        ag = InterviewAgent(llm)
        d = await ag.decide_next(**DECIDE_KWARGS)
        assert d["action"] == "ask_question"
        assert d["question"] == "追问细节？"

    async def test_invalid_decision_falls_back(self):
        # 缺少 question 的非法决策 → 规则回退
        llm = FakeLLM({"action": "ask_question", "strategy": "probe", "question": ""})
        ag = InterviewAgent(llm)
        d = await ag.decide_next(**DECIDE_KWARGS)
        assert d["action"] == "ask_question"
        assert d["question"] == DECIDE_KWARGS["candidates"][0]
        assert "规则回退" in d["reason"]

    async def test_bad_json_falls_back(self):
        ag = InterviewAgent(FakeLLM("无法解析"))
        d = await ag.decide_next(**DECIDE_KWARGS)
        assert d["question"] == DECIDE_KWARGS["candidates"][0]

    async def test_llm_exception_falls_back(self):
        ag = InterviewAgent(FakeLLM(RuntimeError("上游超时")))
        d = await ag.decide_next(**DECIDE_KWARGS)
        assert d["action"] == "ask_question"

    async def test_invalid_strategy_normalized(self):
        llm = FakeLLM({"action": "finish", "strategy": "random_xxx", "question": "", "reason": "够了"})
        ag = InterviewAgent(llm)
        d = await ag.decide_next(**DECIDE_KWARGS)
        assert d["strategy"] == "none"

    async def test_signals_injected_into_prompt(self):
        llm = FakeLLM({"action": "finish", "strategy": "none", "question": "", "reason": "ok"})
        ag = InterviewAgent(llm)
        signals = DecisionSignals(weak_recall=True, summary="回答与话题候选命中弱")
        await ag.decide_next(**DECIDE_KWARGS, signals=signals)
        text = llm.last_messages[0].content
        assert "【信号检测】" in text
        assert "回答与话题候选命中弱" in text


# ── fallback_decision ──
class TestFallback:
    def test_max_rounds_finish(self):
        ag = InterviewAgent(FakeLLM(None))
        d = ag.fallback_decision(["问题1"], asked_rounds=6, max_rounds=6)
        assert d["action"] == "finish"
        assert "轮次上限" in d["reason"]

    def test_no_candidates_finish(self):
        ag = InterviewAgent(FakeLLM(None))
        d = ag.fallback_decision([], asked_rounds=1, max_rounds=6)
        assert d["action"] == "finish"
        assert "题库已耗尽" in d["reason"]

    def test_remedy_signal(self):
        ag = InterviewAgent(FakeLLM(None))
        signals = DecisionSignals(weak_recall=True)
        d = ag.fallback_decision(["问题1"], asked_rounds=1, max_rounds=6, signals=signals)
        assert d["strategy"] == "remedy"

    def test_switch_topic_when_exhausted(self):
        ag = InterviewAgent(FakeLLM(None))
        signals = DecisionSignals(exhausted_topic=True)
        d = ag.fallback_decision(["问题1"], asked_rounds=1, max_rounds=6, signals=signals, probe_streak=2)
        assert d["strategy"] == "switch_topic"
        assert "转向" in d["reason"]


# ── opening ──
class TestOpening:
    async def test_base_opening(self):
        ag = InterviewAgent(FakeLLM(None), persona="严格", difficulty="normal")
        text = await ag.opening("Python 后端工程师")
        assert "Python 后端工程师" in text

    async def test_hard_difficulty_appends_note(self):
        ag = InterviewAgent(FakeLLM(None), persona="严格", difficulty="hard")
        text = await ag.opening("Python 后端工程师")
        assert "高难度" in text

    async def test_hard_without_persona_no_note(self):
        ag = InterviewAgent(FakeLLM(None), persona="", difficulty="hard")
        text = await ag.opening("Python 后端工程师")
        assert "高难度" not in text


# ── 四信号 → 策略（补充现有 test_rag_decisions 未覆盖分支） ──
class TestSignalStrategy:
    def test_low_info_difficulty_weighted(self):
        assert decide_strategy(DecisionSignals(low_information=True), "hard") == "deep_dive"
        assert decide_strategy(DecisionSignals(low_information=True), "easy") == "remedy"
        assert decide_strategy(DecisionSignals(low_information=True), "normal") == "probe"

    def test_project_hint(self):
        assert decide_strategy(DecisionSignals(has_project_hint=True)) == "project_probe"

    def test_weak_recall_priority_over_project(self):
        # weak_recall 优先于 project_hint
        s = DecisionSignals(weak_recall=True, has_project_hint=True)
        assert decide_strategy(s) == "remedy"

    def test_avoid_streak_switch_topic(self):
        s = DecisionSignals(avoid_streak=2)
        assert decide_strategy(s) == "switch_topic"

    def test_is_low_information_whitespace(self):
        assert is_low_information("    ") is True
        long_answer = "我负责了用户登录模块的设计与开发，包含数据库表结构设计、接口联调与性能优化"
        assert is_low_information(long_answer) is False

    def test_analyze_signals_project(self):
        s = analyze_signals("我负责了登录模块的开发", hit_score=10)
        assert s.has_project_hint is True
        assert s.weak_recall is False

    def test_analyze_signals_weak_recall(self):
        s = analyze_signals("我用 Python 写了爬虫，抓取电商数据并清洗入库", hit_score=0, probe_streak=0)
        assert s.weak_recall is True
        assert s.exhausted_topic is False

    def test_analyze_signals_recall_disabled(self):
        # enable_recall=False（谈薪等内置问题库模式）时不触发弱召回
        s = analyze_signals(
            "我用 Python 写了爬虫，抓取电商数据并清洗入库", hit_score=0, enable_recall=False
        )
        assert s.weak_recall is False


# ── 谈薪模式（v1.2：interview_type=salary） ──
class TestSalaryMode:
    async def test_salary_uses_salary_decision_prompt(self):
        llm = FakeLLM({"action": "finish", "strategy": "none", "question": "", "reason": "ok"})
        ag = InterviewAgent(llm, interview_type="salary")
        await ag.decide_next(**DECIDE_KWARGS)
        text = llm.last_messages[0].content
        assert "谈薪" in text
        assert "期望薪资" in text
        assert "不是技术面试" in text

    async def test_normal_mode_keeps_technical_prompt(self):
        llm = FakeLLM({"action": "finish", "strategy": "none", "question": "", "reason": "ok"})
        ag = InterviewAgent(llm, interview_type="normal")
        await ag.decide_next(**DECIDE_KWARGS)
        text = llm.last_messages[0].content
        assert "谈薪" not in text

    async def test_salary_opening_uses_salary_greeting(self):
        ag = InterviewAgent(FakeLLM(None), interview_type="salary")
        text = await ag.opening("Python 后端工程师")
        assert "谈薪" in text
        assert "薪资" in text

    async def test_salary_fallback_normalizes_technical_probe(self):
        # 谈薪模式回退时，deep_dive/project_probe 归一为普通追问
        ag = InterviewAgent(FakeLLM(RuntimeError("超时")), interview_type="salary")
        signals = DecisionSignals(has_project_hint=True)
        d = ag.fallback_decision(["问题1"], asked_rounds=1, max_rounds=6, signals=signals)
        assert d["strategy"] == "probe"


# ── 面试官专属模式（v1.3：interviewer_name 覆盖 interview_type） ──
class TestInterviewerModeOverride:
    async def test_cto_uses_architect_prompt(self):
        llm = FakeLLM({"action": "finish", "strategy": "none", "question": "", "reason": "ok"})
        ag = InterviewAgent(llm, interviewer_name="CTO 技术面")
        await ag.decide_next(**DECIDE_KWARGS)
        text = llm.last_messages[0].content
        assert "CTO" in text
        assert "trade-off" in text

    async def test_hr_uses_hr_prompt_and_bank_source(self):
        llm = FakeLLM({"action": "finish", "strategy": "none", "question": "", "reason": "ok"})
        ag = InterviewAgent(llm, interviewer_name="HR 综合面")
        assert ag.question_source == "hr_bank"
        await ag.decide_next(**DECIDE_KWARGS)
        text = llm.last_messages[0].content
        assert "STAR" in text
        assert "不是技术面试" in text

    async def test_pressure_uses_pressure_prompt(self):
        llm = FakeLLM({"action": "finish", "strategy": "none", "question": "", "reason": "ok"})
        ag = InterviewAgent(llm, interviewer_name="压力面")
        assert ag.question_source == "knowledge"
        await ag.decide_next(**DECIDE_KWARGS)
        text = llm.last_messages[0].content
        assert "压力面试" in text
        assert "质疑" in text

    async def test_switch_uses_switch_prompt_and_bank(self):
        llm = FakeLLM({"action": "finish", "strategy": "none", "question": "", "reason": "ok"})
        ag = InterviewAgent(llm, interviewer_name="转行质疑面试官")
        assert ag.question_source == "switch_bank"
        await ag.decide_next(**DECIDE_KWARGS)
        text = llm.last_messages[0].content
        assert "转行" in text
        assert "可迁移" in text

    async def test_switch_type_without_name_also_uses_switch_prompt(self):
        # 不传面试官名、仅 interview_type=switch 时，同样命中转行配置
        llm = FakeLLM({"action": "finish", "strategy": "none", "question": "", "reason": "ok"})
        ag = InterviewAgent(llm, interview_type="switch")
        assert ag.question_source == "switch_bank"
        await ag.decide_next(**DECIDE_KWARGS)
        assert "转行" in llm.last_messages[0].content

    async def test_all_type_falls_back_to_normal(self):
        # 前端 all 类型无专属模式键 → 兜底 normal
        ag = InterviewAgent(FakeLLM(None), interview_type="all")
        assert ag.question_source == "knowledge"
        text = await ag.opening("Python 后端工程师")
        assert "自我介绍" in text

    def test_non_bank_mode_normalizes_technical_probe(self):
        # 综合/转行模式回退时，deep_dive/project_probe 归一为普通追问
        ag = InterviewAgent(FakeLLM(RuntimeError("超时")), interviewer_name="HR 综合面")
        signals = DecisionSignals(has_project_hint=True)
        d = ag.fallback_decision(["问题1"], asked_rounds=1, max_rounds=6, signals=signals)
        assert d["strategy"] == "probe"

"""面试官 Agent：决策下一步动作并生成问题（Phase 1 文字面试）。

核心方法 decide_next 输出结构化决策：
    {"action": "ask_question"|"finish", "strategy": ..., "question": ..., "reason": ...}

设计（工作包 A）：
- 四信号决策（app.rag.next_question_decision）以"信号检测"段注入 prompt，辅助 LLM 决策；
- LLM 失败时按信号走规则回退（fallback_decision），保证面试流程不中断；
- 工具层由编排器负责装配（app.agents.tools），Agent 只消费决策上下文。
"""
import json
import logging
from typing import Any

from app.agents.prompts import DECISION_PROMPT, OPENING_QUESTION, build_interviewer_sections
from app.llm.base import ChatMessage, LLMProvider
from app.rag.next_question_decision import DecisionSignals, build_signal_section, decide_strategy

logger = logging.getLogger(__name__)

STRATEGIES = {"deep_dive", "probe", "remedy", "switch_topic", "project_probe", "none"}


def _extract_json(raw: str) -> Any:
    """从 LLM 输出中提取 JSON（容忍代码块包裹与前后杂质）。"""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


class InterviewAgent:
    """封装面试官决策逻辑。

    persona/style/difficulty：面试官角色与难度档位（v1.1），
    未配置时为空/默认值，保持原有通用人设与标准难度。
    """

    def __init__(
        self,
        llm: LLMProvider,
        persona: str = "",
        style: str = "",
        difficulty: str = "normal",
    ):
        self._llm = llm
        self._persona = persona
        self._style = style
        self._difficulty = difficulty
        self._interviewer_sections = build_interviewer_sections(persona, style, difficulty)

    async def decide_next(
        self,
        *,
        position_name: str,
        position_skills: list[str],
        resume_brief: str,
        history_text: str,
        latest_answer: str,
        candidates: list[str],
        asked_rounds: int,
        max_rounds: int,
        probe_streak: int = 0,
        signals: DecisionSignals | None = None,
        coverage_hint: str = "",
    ) -> dict:
        """生成下一轮决策（LLM 优先，失败走规则回退）。

        probe_streak：当前话题已连续追问的轮数，≥2 时 prompt 强制换话题。
        signals：四信号快照（工作包 A），非空时注入 prompt 辅助决策。
        coverage_hint：技能覆盖提示（工具③输出），用于引导换话题方向。
        """
        candidates_text = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(candidates[:8])) or "（暂无，可自行拟定）"
        signal_section = build_signal_section(signals) if signals else ""
        prompt = DECISION_PROMPT.format(
            position_name=position_name,
            interviewer_sections=self._interviewer_sections or "（按通用面试官人设与标准难度进行）",
            position_skills="、".join(position_skills[:12]) or "（未提供）",
            resume_brief=(resume_brief or "")[:800],
            history=history_text or "（无）",
            latest_answer=(latest_answer or "")[:600],
            candidates=candidates_text,
            asked_rounds=asked_rounds,
            max_rounds=max_rounds,
            probe_streak=probe_streak,
            signal_section=signal_section,
            coverage_hint=coverage_hint or "",
        )
        try:
            raw = await self._llm.achat(
                [ChatMessage("user", prompt)],
                temperature=0,
                max_tokens=800,
            )
            decision = _extract_json(raw)
            if not self._validate(decision):
                raise ValueError("decision 字段不合法")
            return decision
        except Exception as exc:  # noqa: BLE001 - 兜底保证流程不中断
            logger.warning("LLM 决策失败，使用规则回退: %s", exc)
            return self.fallback_decision(
                candidates, asked_rounds, max_rounds,
                signals=signals, probe_streak=probe_streak,
            )

    def _validate(self, d: dict) -> bool:
        if not isinstance(d, dict):
            return False
        if d.get("action") not in ("ask_question", "finish"):
            return False
        if d.get("strategy") not in STRATEGIES:
            d["strategy"] = "none"
        if d.get("action") == "ask_question" and not (d.get("question") or "").strip():
            return False
        return True

    def fallback_decision(
        self,
        candidates: list[str],
        asked_rounds: int,
        max_rounds: int,
        signals: DecisionSignals | None = None,
        probe_streak: int = 0,
    ) -> dict:
        """规则回退：结合四信号决策出题，耗尽或到上限则结束。"""
        if asked_rounds >= max_rounds:
            return {"action": "finish", "strategy": "none", "question": "", "reason": "达到轮次上限"}
        if not candidates:
            return {"action": "finish", "strategy": "none", "question": "", "reason": "题库已耗尽"}
        strategy = decide_strategy(signals, self._difficulty) if signals else "none"
        reason = "规则回退：按题库顺序出题"
        if strategy == "switch_topic" and probe_streak >= 2:
            reason = "规则回退：连续追问过深，转向未覆盖方向"
        elif strategy == "remedy":
            reason = "规则回退：检测到回答偏题/信息量低，温和拉回正题"
        return {
            "action": "ask_question",
            "strategy": strategy,
            "question": candidates[0],
            "reason": reason,
        }

    async def opening(self, position_name: str) -> str:
        """生成开场问题（固定开场白 + 可选角色开场白，保证稳定）。"""
        base = OPENING_QUESTION.format(position_name=position_name)
        if self._persona and self._difficulty == "hard":
            # 困难档 + 有角色设定：在开场追加一句角色化的开场白
            return f"{base}\n\n（本场为高难度面试，问题会更有挑战性，请做好准备。）"
        return base

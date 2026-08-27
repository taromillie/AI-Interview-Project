"""面试编排器：驱动 Interview 状态机（Phase 1 文字面试）。

状态流转：created → asking →（asking ↔）→ finishing → reported
每个动作返回 SSE 事件 dict：
    {"event": "question", "data": {"round", "strategy", "question", "finished": False}}
    {"event": "finished", "data": {"message", "report_id"}}
"""
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.interview_agent import InterviewAgent
from app.core.exceptions import AppError
from app.llm.base import LLMProvider
from app.models.interview import Interview, InterviewMessage, Report
from app.models.position import Position
from app.models.resume import Resume
from app.models.user import User
from app.rag.retriever import select_candidates
from app.services.feedback import fallback_report, generate_report

logger = logging.getLogger(__name__)

VALID_STATUS = {"created", "asking", "finishing", "reported"}


class InterviewOrchestrator:
    """一次面试会话的编排器。"""

    def __init__(self, db: Session, user: User, interview: Interview, llm: LLMProvider):
        self.db = db
        self.user = user
        self.interview = interview
        self.llm = llm
        self.agent = InterviewAgent(llm)
        self.position: Position | None = None
        self.resume: Resume | None = None
        if interview.position_id:
            self.position = db.get(Position, interview.position_id)
        if interview.resume_id:
            self.resume = db.get(Resume, interview.resume_id)

    # ---------- 内部工具 ----------

    def _save_message(self, role: str, content: str, strategy: str | None = None) -> None:
        self.db.add(
            InterviewMessage(
                interview_id=self.interview.id,
                role=role,
                content=content,
                strategy=strategy,
            )
        )

    def _messages(self) -> list[InterviewMessage]:
        return list(
            self.db.scalars(
                select(InterviewMessage)
                .where(InterviewMessage.interview_id == self.interview.id)
                .order_by(InterviewMessage.id)
            )
        )

    def _asked_rounds(self) -> int:
        """已问过的面试官问题数（assistant 消息）。"""
        return sum(1 for m in self._messages() if m.role == "assistant")

    def _history_text(self, limit: int = 6) -> str:
        lines = [
            f"{'面试官' if m.role == 'assistant' else '候选人'}：{m.content}"
            for m in self._messages()[-limit:]
        ]
        return "\n".join(lines)

    def _resume_brief(self) -> str:
        if self.resume is None:
            return ""
        brief = (self.resume.parsed_json or {}).get("brief", "")
        return brief or (self.resume.raw_text or "")[:300]

    def _position_skills(self) -> list[str]:
        return self.position.skills if self.position else []

    def _position_name(self) -> str:
        return self.position.name if self.position else "通用岗位"

    # ---------- 状态机动作 ----------

    async def start(self) -> dict:
        """进入 asking，发出开场问题。"""
        if self.interview.status not in ("created", "asking"):
            raise AppError("面试已结束，无法开始")
        if self.interview.status == "created":
            question = await self.agent.opening(self._position_name())
            self.interview.status = "asking"
            self._save_message("assistant", question, "opening")
            self.db.commit()
        return {
            "event": "question",
            "data": {
                "round": 1,
                "strategy": "opening",
                "question": self._last_question(),
                "finished": False,
            },
        }

    def _last_question(self) -> str:
        msgs = self._messages()
        for m in reversed(msgs):
            if m.role == "assistant":
                return m.content
        return ""

    async def answer(self, content: str) -> dict:
        """提交候选人回答，决策下一问或结束。"""
        if self.interview.status not in ("asking", "created"):
            raise AppError("当前状态不可回答")
        if self.interview.status == "created":
            await self.start()

        self._save_message("user", content, None)
        asked_rounds = self._asked_rounds()

        if asked_rounds >= self.interview.max_rounds:
            self.db.commit()
            return await self.finish()

        asked_ids = {m.id for m in self._messages()}
        candidates = select_candidates(
            self.db,
            self.interview.position_id,
            asked_ids,
            answer_text=content,
            top_n=8,
        )
        candidate_texts = [c.question for c in candidates]

        decision = await self.agent.decide_next(
            position_name=self._position_name(),
            position_skills=self._position_skills(),
            resume_brief=self._resume_brief(),
            history_text=self._history_text(),
            latest_answer=content,
            candidates=candidate_texts,
            asked_rounds=asked_rounds,
            max_rounds=self.interview.max_rounds,
        )

        if decision.get("action") == "finish" or asked_rounds >= self.interview.max_rounds:
            self.db.commit()
            return await self.finish()

        question = (decision.get("question") or "").strip()
        if not question:
            question = self.agent.fallback_decision(
                candidate_texts, asked_rounds, self.interview.max_rounds
            ).get("question", "请再详细讲讲你的思路。")

        strategy = decision.get("strategy", "none")
        self._save_message("assistant", question, strategy)
        self.db.commit()
        return {
            "event": "question",
            "data": {
                "round": asked_rounds + 1,
                "strategy": strategy,
                "question": question,
                "finished": False,
            },
        }

    async def finish(self) -> dict:
        """结束面试并生成复盘报告（LLM 失败走规则降级）。"""
        if self.interview.status not in ("asking", "created", "finishing"):
            raise AppError("面试已结束")
        if self.interview.status != "finishing":
            self.interview.status = "finishing"
            self.db.commit()

        messages = self._messages()
        try:
            data = await generate_report(
                llm=self.llm,
                position_name=self._position_name(),
                position_skills=self._position_skills(),
                resume_brief=self._resume_brief(),
                messages=messages,
            )
        except Exception as exc:  # noqa: BLE001 - 保证一定有报告
            logger.warning("LLM 报告生成失败，使用规则降级: %s", exc)
            data = fallback_report(messages)

        report = Report(
            interview_id=self.interview.id,
            overall_score=data.get("overall_score", 0.0),
            dimensions=data.get("dimensions", {}),
            question_feedback=data.get("question_feedback", []),
            weak_points=data.get("weak_points", []),
        )
        self.interview.status = "reported"
        self.interview.finished_at = datetime.now()
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        return {
            "event": "finished",
            "data": {
                "message": data.get("summary") or "面试结束，复盘报告已生成。",
                "report_id": report.id,
            },
        }

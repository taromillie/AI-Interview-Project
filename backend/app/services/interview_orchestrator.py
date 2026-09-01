"""面试编排器：驱动 Interview 状态机（Phase 1 文字面试）。

状态流转：created → asking →（asking ↔）→ finishing → reported
每个动作返回 SSE 事件 dict：
    {"event": "question", "data": {"round", "strategy", "question", "finished": False}}
    {"event": "finished", "data": {"message", "report_id"}}
"""
import json
import logging
import threading
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.agents.interview_agent import InterviewAgent
from app.agents.prompts import BANK_SOURCES
from app.agents.tools import (
    ToolCallGuard,
    get_coverage,
    get_resume_evidence,
    search_knowledge,
)
from app.core.exceptions import AppError
from app.llm.base import LLMProvider
from app.models.interview import Interview, InterviewMessage, Report
from app.models.interviewer import Interviewer
from app.models.position import Position
from app.models.resume import Resume
from app.models.user import User
from app.rag.embedding import get_embedding_provider
from app.rag.next_question_decision import analyze_signals, is_low_information
from app.rag.retriever import hit_score

logger = logging.getLogger(__name__)

VALID_STATUS = {"created", "asking", "finishing", "reported"}

# 视为"追问当前话题"的策略：命中这些策略且连续出现即表示在死磕一个点
PROBE_STRATEGIES = {"deep_dive", "probe", "project_probe"}
# 同一方向允许的最大连续追问轮数，超过后强制切换话题
MAX_PROBE_STREAK = 3

# 占位报告的总评标记：后台生成完成后会被真实总评覆盖，前端据此轮询
REPORT_PENDING_SUMMARY = "报告生成中，请稍后刷新查看…"

# 面试结束语（口语化、有温度，随机取一个）
FAREWELL_VARIANTS = [
    "好的，今天关于{position}的面试就到这儿。很感谢你刚才这些回答，聊得挺深入，也让我看到了你对这个方向的理解。我先把咱们的对话整理成一份复盘报告——里面有你的亮点，也有可以再打磨的地方，稍等片刻。",
    "行，今天关于{position}的问题就问到这里。谢谢你的坦诚分享，整个过程收获不小。我花一两分钟把这次面试整理成复盘报告，包括做得好的和可以改进的，马上就好。",
    "好，咱们今天的面试就到此结束。感谢你认真回答每一个问题，聊下来能感觉到你有自己的积累。接下来我会生成一份复盘报告，帮你把这次表现梳理清楚，稍等一下。",
]


class InterviewOrchestrator:
    """一次面试会话的编排器。"""

    def __init__(self, db: Session, user: User, interview: Interview, llm: LLMProvider):
        self.db = db
        self.user = user
        self.interview = interview
        self.llm = llm
        self.position: Position | None = None
        self.resume: Resume | None = None
        if interview.position_id:
            self.position = db.get(Position, interview.position_id)
        if interview.resume_id:
            self.resume = db.get(Resume, interview.resume_id)
        # v1.1：加载面试官角色与难度，注入 Agent 人设
        interviewer = db.get(Interviewer, interview.interviewer_id) if interview.interviewer_id else None
        self.agent = InterviewAgent(
            llm,
            persona=interviewer.persona if interviewer else "",
            style=interviewer.style if interviewer else "",
            difficulty=interview.difficulty or "normal",
            interview_type=interview.interview_type or "normal",
            interviewer_name=interviewer.name if interviewer else "",
        )

    # ---------- 内部工具 ----------

    def _save_message(
        self,
        role: str,
        content: str,
        strategy: str | None = None,
        evidence_atom_ids: list[int] | None = None,
    ) -> None:
        self.db.add(
            InterviewMessage(
                interview_id=self.interview.id,
                role=role,
                content=content,
                strategy=strategy,
                evidence_atom_ids=evidence_atom_ids or [],
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

    def _asked_rounds(self, msgs: list[InterviewMessage]) -> int:
        """已问过的面试官问题数（assistant 消息）。"""
        return sum(1 for m in msgs if m.role == "assistant")

    def _probe_streak(self, msgs: list[InterviewMessage]) -> int:
        """当前话题连续追问轮数：从最近的 assistant 消息向前数连续追问策略。"""
        streak = 0
        for m in reversed(msgs):
            if m.role != "assistant":
                continue
            if m.strategy in PROBE_STRATEGIES:
                streak += 1
            else:
                break
        return streak

    def _avoid_streak(self, msgs: list[InterviewMessage]) -> int:
        """连续低信息/回避回答轮数：从最近的 user 消息向前数。"""
        streak = 0
        for m in reversed(msgs):
            if m.role != "user":
                continue
            if is_low_information(m.content):
                streak += 1
            else:
                break
        return streak

    def _history_text(self, msgs: list[InterviewMessage], limit: int = 6) -> str:
        lines = [
            f"{'面试官' if m.role == 'assistant' else '候选人'}：{m.content}"
            for m in msgs[-limit:]
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
        # 优先使用自定义/JD 目标岗位；其次题库岗位；最后通用兜底
        target = (self.interview.config or {}).get("target_position")
        if target:
            return str(target)
        return self.position.name if self.position else "通用岗位"

    def _question_source(self) -> str:
        """当前面试官命中的问题来源键（knowledge=技术题库检索；*_bank=内置问题库）。"""
        return self.agent.question_source

    def _farewell_text(self) -> str:
        import random

        return random.choice(FAREWELL_VARIANTS).format(position=self._position_name())

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
                "question": self._last_question(self._messages()),
                "finished": False,
            },
        }

    def _last_question(self, msgs: list[InterviewMessage]) -> str:
        for m in reversed(msgs):
            if m.role == "assistant":
                return m.content
        return ""

    def _cache_answer_result(self, config: dict, request_id: str, result: dict) -> None:
        """记录回答的幂等键与结果，供断线重发去重（重放，不重复记录回答）。"""
        config["last_answer_request_id"] = request_id
        config["last_answer_result"] = json.dumps(result, ensure_ascii=False)
        self.interview.config = config
        self.db.commit()

    async def answer(self, content: str, request_id: str | None = None) -> dict:
        """提交候选人回答，决策下一问或结束。

        request_id 为断线重发去重的幂等键：同一 id 的重发直接重放上次结果，
        避免回答被重复记录、轮数被重复推进（面试断线可恢复的关键）。
        """
        config = self.interview.config or {}
        if request_id and config.get("last_answer_request_id") == request_id:
            cached = config.get("last_answer_result")
            if cached:
                try:
                    return json.loads(cached)
                except (TypeError, ValueError):
                    pass

        if self.interview.status not in ("asking", "created"):
            raise AppError("当前状态不可回答")
        if self.interview.status == "created":
            await self.start()

        self._save_message("user", content, None)
        # 会话消息只查一次，后续统计/决策全部复用，避免 N+1
        msgs = self._messages()
        asked_rounds = self._asked_rounds(msgs)

        if asked_rounds >= self.interview.max_rounds:
            self.db.commit()
            result = await self.finish()
            if request_id:
                self._cache_answer_result(config, request_id, result)
            return result

        # 已问过的题目 id 从消息的证据原子中收集（消息 id 与原子 id 各自自增，不能混用）
        asked_ids = set()
        for m in msgs:
            asked_ids.update(m.evidence_atom_ids or [])
        probe_streak = self._probe_streak(msgs)

        # ---- 工作包 A：有边界工具装配（只读 + 单轮≤3 次调用） ----
        guard = ToolCallGuard()
        embedder = get_embedding_provider()

        source = self._question_source()
        bank = BANK_SOURCES.get(source)
        if bank is not None:
            # 内置问题库模式（谈薪/综合/转行）：候选来自对应题库（剔除已问），不检索技术题库
            asked_texts = {m.content for m in msgs if m.role == "assistant"}
            candidate_texts = [q for q in bank if q not in asked_texts]
            candidates: list = []
            hit = 0
            coverage_hint = ""
        else:
            # 工具① 候选检索（向量增强 + 关键词降级）
            tool_res = await search_knowledge(
                self.db,
                self.interview.position_id,
                asked_ids,
                answer_text=content,
                top_n=8,
                embedder=embedder,
                guard=guard,
            )
            candidates = tool_res.data or []
            candidate_texts = [c.question for c in candidates]

            # 工具③ 技能覆盖度提示（辅助换话题方向）
            coverage_res = get_coverage(
                self._position_skills(),
                [m.content for m in msgs if m.role == "assistant"],
                guard=guard,
            )
            coverage = coverage_res.data or {}
            coverage_hint = coverage.get("hint", "")
            hit = max((hit_score(c, content) for c in candidates), default=0)

        # 工具② 简历证据（优先于静态 brief，保证决策上下文新鲜）
        resume_evidence = get_resume_evidence(self.resume, guard=guard).data or ""

        # ---- 工作包 A：四信号决策 ----
        signals = analyze_signals(
            content,
            hit_score=hit,
            probe_streak=probe_streak,
            avoid_streak=self._avoid_streak(msgs),
            enable_recall=source == "knowledge",
        )

        decision = await self.agent.decide_next(
            position_name=self._position_name(),
            position_skills=self._position_skills(),
            resume_brief=resume_evidence or self._resume_brief(),
            history_text=self._history_text(msgs),
            latest_answer=content,
            candidates=candidate_texts,
            asked_rounds=asked_rounds,
            max_rounds=self.interview.max_rounds,
            probe_streak=probe_streak,
            signals=signals,
            coverage_hint=coverage_hint,
        )

        # 内置问题库模式（谈薪/综合/转行）：技术面试专用策略归一为普通追问
        if source != "knowledge" and decision.get("strategy") == "project_probe":
            decision["strategy"] = "probe"

        # 强制兜底：同一方向已连续追问超过上限，必须切换话题，不再死磕
        if decision.get("strategy") in PROBE_STRATEGIES and probe_streak >= MAX_PROBE_STREAK:
            decision["strategy"] = "switch_topic"
            if candidate_texts:
                decision["question"] = candidate_texts[0]
                decision["reason"] = "连续追问超过上限，强制切换到未覆盖的新方向"
            else:
                decision["reason"] = "连续追问超过上限，改为开放式换题"

        if decision.get("action") == "finish" or asked_rounds >= self.interview.max_rounds:
            self.db.commit()
            result = await self.finish()
            if request_id:
                self._cache_answer_result(config, request_id, result)
            return result

        question = (decision.get("question") or "").strip()
        if not question:
            question = self.agent.fallback_decision(
                candidate_texts, asked_rounds, self.interview.max_rounds
            ).get("question", "请再详细讲讲你的思路。")

        strategy = decision.get("strategy", "none")
        self._save_message(
            "assistant",
            question,
            strategy,
            evidence_atom_ids=[c.id for c in candidates],
        )
        self.db.commit()
        result = {
            "event": "question",
            "data": {
                "round": asked_rounds + 1,
                "strategy": strategy,
                "question": question,
                "finished": False,
            },
        }
        if request_id:
            self._cache_answer_result(config, request_id, result)
        return result

    async def finish(self) -> dict:
        """结束面试：立即返回，复盘报告在后台线程生成，接口不再长时间等待 LLM。

        幂等保护：通过原子状态迁移 created/asking → finishing 抢占收尾权，
        并发/重复调用只有第一次能成功，其余直接拒绝，避免重复触发报告任务。
        """
        if self.interview.status == "reported":
            raise AppError("面试已结束")
        if self.interview.status == "finishing":
            raise AppError("面试已结束，报告正在生成")
        claimed = self.db.execute(
            update(Interview)
            .where(Interview.id == self.interview.id)
            .where(Interview.status.in_(("created", "asking")))
            .values(status="finishing")
        )
        self.db.commit()
        if claimed.rowcount != 1:
            raise AppError("面试已结束，请勿重复操作")
        self.db.refresh(self.interview)

        # 面试官结束语：先保存（后台报告任务会排除 farewell 消息，避免被当作候选问题分析）
        farewell = self._farewell_text()
        self._save_message("assistant", farewell, "farewell")

        # 先落一条占位报告，报告页可立即展示"生成中"，后台任务完成后更新为真实内容
        report = Report(
            interview_id=self.interview.id,
            overall_score=0.0,
            dimensions={},
            question_feedback=[],
            weak_points=[],
            summary=REPORT_PENDING_SUMMARY,
            coverage={"covered": [], "uncovered": []},
            learning_path=[],
            status="pending",
        )
        self.interview.status = "reported"
        self.interview.finished_at = datetime.now()
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        interview_id = self.interview.id

        def _run() -> None:
            # 延迟导入：避免 workers.report 与本模块循环导入
            from app.workers.report import generate_report_task

            generate_report_task(interview_id)

        threading.Thread(target=_run, daemon=True).start()

        return {
            "event": "finished",
            "data": {
                "message": "面试结束，复盘报告正在生成。",
                "report_id": report.id,
                "farewell": farewell,
            },
        }

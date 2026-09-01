"""复盘报告后台生成任务。"""
import asyncio
import logging

from app.core.db import SessionLocal
from app.models.interview import Interview, InterviewMessage, Report
from app.models.user import User
from app.services.feedback import fallback_report, generate_report
from app.services.interview_orchestrator import InterviewOrchestrator
from app.services.llm_utils import get_llm_for_user

logger = logging.getLogger(__name__)


def generate_report_task(interview_id: int) -> None:
    """在独立会话中生成报告，适合后台线程 / FastAPI BackgroundTasks。"""
    db = SessionLocal()
    try:
        interview = db.get(Interview, interview_id)
        if interview is None:
            return
        existing = (
            db.query(Report).filter(Report.interview_id == interview_id).first()
        )
        # 报告已生成（AI 完整报告或已降级）则跳过；pending/failed 由本任务覆盖更新（failed 支持重试）
        if existing is not None and existing.status in ("ready", "fallback"):
            return
        messages = list(
            db.query(InterviewMessage)
            .filter(InterviewMessage.interview_id == interview_id)
            .order_by(InterviewMessage.id)
            .all()
        )
        # 排除面试官结束语，避免被当作候选问题分析
        messages = [m for m in messages if not (m.role == "assistant" and m.strategy == "farewell")]
        # 只分析"已作答"的问答：结束面试时最后一个问题若尚未回答，不将其计入复盘评分
        last_answer = next(
            (i for i in range(len(messages) - 1, -1, -1) if messages[i].role == "user"),
            None,
        )
        messages = messages[: last_answer + 1] if last_answer is not None else []
        llm = get_llm_for_user(db, interview.user_id)
        used_fallback = False
        if llm is None:
            logger.warning("未配置 LLM，使用规则降级报告: interview_id=%s", interview_id)
            data = fallback_report(messages)
            used_fallback = True
        else:
            user = db.get(User, interview.user_id)
            if user is None:
                return
            orchestrator = InterviewOrchestrator(db, user, interview, llm)
            try:
                position_name = (
                    orchestrator.position.name
                    if orchestrator.position
                    else (interview.config or {}).get("target_position") or "目标岗位"
                )
                data = asyncio.run(
                    generate_report(
                        llm=llm,
                        position_name=position_name,
                        position_skills=orchestrator._position_skills(),
                        resume_brief=orchestrator._resume_brief(),
                        messages=messages,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("后台 LLM 报告失败，使用规则降级: %s", exc)
                data = fallback_report(messages)
                used_fallback = True
        report = existing or Report(interview_id=interview_id)
        if report not in db:
            db.add(report)
        report.overall_score = data.get("overall_score", 0.0)
        report.dimensions = data.get("dimensions", {})
        report.question_feedback = data.get("question_feedback", [])
        report.weak_points = data.get("weak_points", [])
        report.summary = data.get("summary") or ""
        report.coverage = data.get("coverage", {"covered": [], "uncovered": []})
        report.learning_path = data.get("learning_path", [])
        # 状态：LLM 全程可用 → ready；任意环节降级 → fallback（前端可提示并可重新生成）
        report.status = "fallback" if used_fallback else "ready"
        interview.status = "reported"
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("后台报告任务失败: interview_id=%s", interview_id)
        # 报告失败显式标记 failed，前端可识别并触发重新生成
        try:
            report = (
                db.query(Report).filter(Report.interview_id == interview_id).first()
            )
            if report is not None:
                report.status = "failed"
                db.commit()
        except Exception:
            db.rollback()
            logger.exception("标记报告失败状态时出错: interview_id=%s", interview_id)
    finally:
        db.close()

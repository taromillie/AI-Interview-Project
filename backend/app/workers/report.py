"""复盘报告后台生成任务。"""
import asyncio
import logging

from app.core.db import SessionLocal
from app.models.interview import Interview, InterviewMessage, Report
from app.models.user import User
from app.services.feedback import fallback_report, generate_report
from app.services.llm_utils import get_llm_for_user
from app.services.interview_orchestrator import InterviewOrchestrator

logger = logging.getLogger(__name__)


def generate_report_task(interview_id: int) -> None:
    """在独立会话中生成报告，适合 FastAPI BackgroundTasks。"""
    db = SessionLocal()
    try:
        interview = db.get(Interview, interview_id)
        if interview is None or interview.status == "reported":
            return
        messages = list(
            db.query(InterviewMessage)
            .filter(InterviewMessage.interview_id == interview_id)
            .order_by(InterviewMessage.id)
            .all()
        )
        llm = get_llm_for_user(db, interview.user_id)
        if llm is None:
            data = fallback_report(messages)
        else:
            user = db.get(User, interview.user_id)
            if user is None:
                return
            orchestrator = InterviewOrchestrator(db, user, interview, llm)
            try:
                position_name = orchestrator.position.name if orchestrator.position else interview.target_position or "目标岗位"
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
        report = db.query(Report).filter(Report.interview_id == interview_id).first()
        if report is None:
            report = Report(interview_id=interview_id)
            db.add(report)
        report.overall_score = data.get("overall_score", 0.0)
        report.dimensions = data.get("dimensions", {})
        report.question_feedback = data.get("question_feedback", [])
        report.weak_points = data.get("weak_points", [])
        interview.status = "reported"
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("后台报告任务失败: interview_id=%s", interview_id)
    finally:
        db.close()

"""复盘报告接口。"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.interview import Interview, Report
from app.services.interview_orchestrator import REPORT_PENDING_SUMMARY
from app.workers.report import generate_report_task
from app.models.user import User
from app.schemas.interview import ReportOut

router = APIRouter(prefix="/reports", tags=["复盘报告"])


def _is_pending_report(report: Report | None) -> bool:
    """总评为占位标记即表示报告仍在后台生成。"""
    return report is not None and report.summary == REPORT_PENDING_SUMMARY


@router.post("/interviews/{interview_id}/generate", status_code=202)
def enqueue_report(
    interview_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交后台报告任务，立即返回可轮询的处理中状态。"""
    interview = db.get(Interview, interview_id)
    if interview is None or interview.user_id != user.id:
        raise HTTPException(status_code=404, detail="面试不存在")
    existing = db.query(Report).filter(Report.interview_id == interview_id).first()
    if existing and not _is_pending_report(existing):
        return {"status": "reported", "interview_id": interview_id}
    if existing is None:
        interview.status = "finishing"
        db.commit()
    # 占位报告存在（生成中/上次任务中断）：重新入队确保完成
    background_tasks.add_task(generate_report_task, interview_id)
    return {"status": "processing", "interview_id": interview_id}


@router.get("/interviews/{interview_id}/status")
def report_status(
    interview_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """返回报告生成状态，供前端轮询。"""
    interview = db.get(Interview, interview_id)
    if interview is None or interview.user_id != user.id:
        raise HTTPException(status_code=404, detail="面试不存在")
    report = db.query(Report).filter(Report.interview_id == interview_id).first()
    if _is_pending_report(report):
        status = "processing"
    elif report:
        status = "reported"
    else:
        status = "processing" if interview.status == "finishing" else interview.status
    return {
        "status": status,
        "interview_id": interview_id,
        "report_id": report.id if report else None,
    }


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="报告不存在")
    interview = db.get(Interview, report.interview_id)
    if interview is None or interview.user_id != user.id:
        raise HTTPException(status_code=404, detail="报告不存在")
    return report

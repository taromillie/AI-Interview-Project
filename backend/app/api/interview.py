"""模拟面试接口（Phase 1 文字面试，含 SSE 对话流）。

SSE 事件协议：
- preparing / thinking：状态提示
- question：{"round", "strategy", "question", "finished": false}
- finished：{"message", "report_id"}
- error：{"message"}
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.exceptions import AppError
from app.models.interview import Interview, InterviewMessage, Report
from app.models.interviewer import Interviewer
from app.models.position import Position
from app.models.user import User
from app.schemas.interview import (
    AnswerRequest,
    InterviewCreateRequest,
    InterviewDetailOut,
    InterviewMessageOut,
    InterviewOut,
)
from app.services.interview_orchestrator import InterviewOrchestrator
from app.services.llm_utils import require_llm

router = APIRouter(prefix="/interviews", tags=["模拟面试"])


def _own_interview(db: Session, user: User, interview_id: int) -> Interview:
    interview = db.get(Interview, interview_id)
    if interview is None or interview.user_id != user.id:
        raise HTTPException(404, "面试不存在")
    return interview


def _make_out(db: Session, interview: Interview) -> InterviewOut:
    position_name = None
    if interview.position_id:
        pos = db.get(Position, interview.position_id)
        position_name = pos.name if pos else None
    interviewer_name = None
    if interview.interviewer_id:
        iv = db.get(Interviewer, interview.interviewer_id)
        interviewer_name = iv.name if iv else None
    report = db.scalar(select(Report).where(Report.interview_id == interview.id))
    message_count = db.scalar(
        select(func.count())
        .select_from(InterviewMessage)
        .where(InterviewMessage.interview_id == interview.id)
    )
    return InterviewOut(
        id=interview.id,
        position_id=interview.position_id,
        position_name=position_name,
        target_position=(interview.config or {}).get("target_position"),
        resume_id=interview.resume_id,
        interviewer_id=interview.interviewer_id,
        interviewer_name=interviewer_name,
        difficulty=interview.difficulty,
        mode=interview.mode,
        interview_type=interview.interview_type,
        status=interview.status,
        max_rounds=interview.max_rounds,
        created_at=interview.created_at,
        report_id=report.id if report else None,
        overall_score=report.overall_score if report else None,
        message_count=message_count or 0,
    )


@router.post("", response_model=InterviewOut, status_code=201)
def create_interview(
    payload: InterviewCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建面试会话。"""
    require_llm(db, user)
    if payload.position_id:
        if db.get(Position, payload.position_id) is None:
            raise HTTPException(404, "所选岗位不存在")
    if payload.target_position:
        # 自定义/JD 岗位名存入 config，供面试官作为岗位上下文
        payload.config = {**(payload.config or {}), "target_position": payload.target_position.strip()[:80]}
    # 面试官角色：未指定时按面试模式自动选择匹配的内置角色
    interviewer_id = payload.interviewer_id
    if interviewer_id is not None and db.get(Interviewer, interviewer_id) is None:
        raise HTTPException(404, "所选面试官不存在")
    if interviewer_id is None:
        default = db.scalars(
            select(Interviewer).where(
                Interviewer.is_public == True,  # noqa: E712
                (Interviewer.interview_type == "all") | (Interviewer.interview_type == payload.interview_type),
            ).order_by(Interviewer.id).limit(1)
        ).first()
        interviewer_id = default.id if default else None
    interview = Interview(
        user_id=user.id,
        position_id=payload.position_id,
        resume_id=payload.resume_id,
        interviewer_id=interviewer_id,
        difficulty=payload.difficulty,
        mode=payload.mode,
        interview_type=payload.interview_type,
        max_rounds=payload.max_rounds,
        config=payload.config,
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return _make_out(db, interview)


def _sse(result):
    async def gen():
        try:
            outcome = await result
        except AppError as exc:
            yield {"event": "error", "data": json.dumps({"message": str(exc)}, ensure_ascii=False)}
            return
        yield {
            "event": outcome["event"],
            "data": json.dumps(outcome["data"], ensure_ascii=False),
        }

    return EventSourceResponse(gen())


@router.post("/{interview_id}/start")
async def start_interview(
    interview_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """开始面试，SSE 返回开场问题。"""
    interview = _own_interview(db, user, interview_id)
    llm = require_llm(db, user)
    orchestrator = InterviewOrchestrator(db, user, interview, llm)

    async def gen():
        yield {
            "event": "preparing",
            "data": json.dumps({"message": "面试官已就绪，正在出题…"}, ensure_ascii=False),
        }
        outcome = await orchestrator.start()
        yield {
            "event": outcome["event"],
            "data": json.dumps(outcome["data"], ensure_ascii=False),
        }

    return EventSourceResponse(gen())


@router.post("/{interview_id}/answer")
async def submit_answer(
    interview_id: int,
    payload: AnswerRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交回答，SSE 返回下一问或结束事件。"""
    interview = _own_interview(db, user, interview_id)
    llm = require_llm(db, user)
    orchestrator = InterviewOrchestrator(db, user, interview, llm)

    async def gen():
        yield {
            "event": "thinking",
            "data": json.dumps({"message": "面试官正在思考…"}, ensure_ascii=False),
        }
        try:
            outcome = await orchestrator.answer(payload.content)
        except AppError as exc:
            yield {"event": "error", "data": json.dumps({"message": str(exc)}, ensure_ascii=False)}
            return
        # 面试结束时：先发面试官结束语，再发 finished
        farewell = (outcome.get("data") or {}).pop("farewell", None)
        if farewell:
            yield {"event": "farewell", "data": json.dumps({"message": farewell}, ensure_ascii=False)}
        yield {
            "event": outcome["event"],
            "data": json.dumps(outcome["data"], ensure_ascii=False),
        }

    return EventSourceResponse(gen())


@router.post("/{interview_id}/finish")
async def finish_interview(
    interview_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """结束面试并生成复盘报告。"""
    interview = _own_interview(db, user, interview_id)
    llm = require_llm(db, user)
    orchestrator = InterviewOrchestrator(db, user, interview, llm)
    outcome = await orchestrator.finish()
    farewell = (outcome.get("data") or {}).pop("farewell", None)
    return {"status": "reported", "farewell": farewell, **outcome["data"]}


@router.get("", response_model=list[InterviewOut])
def list_interviews(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(Interview)
        .where(Interview.user_id == user.id)
        .order_by(Interview.id.desc())
        .limit(50)
    ).all()
    return [_make_out(db, i) for i in rows]


@router.get("/{interview_id}", response_model=InterviewDetailOut)
def interview_detail(
    interview_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """面试详情：完整问答流 + 复盘报告（用于历史复盘）。"""
    interview = _own_interview(db, user, interview_id)
    messages = db.scalars(
        select(InterviewMessage)
        .where(InterviewMessage.interview_id == interview.id)
        .order_by(InterviewMessage.id)
    ).all()
    report = db.scalar(select(Report).where(Report.interview_id == interview.id))
    base = _make_out(db, interview)
    return InterviewDetailOut(
        **base.model_dump(),
        messages=[InterviewMessageOut.model_validate(m) for m in messages],
        report=report,
    )

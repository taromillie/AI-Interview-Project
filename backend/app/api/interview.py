"""模拟面试接口（Phase 1 文字面试，含 SSE 对话流）。

SSE 事件协议：
- preparing / thinking：状态提示
- question：{"round", "strategy", "question", "finished": false}
- finished：{"message", "report_id"}
- error：{"message"}
"""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.exceptions import AppError
from app.core.rate_limit import limiter
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
from app.repositories import InterviewRepository

router = APIRouter(prefix="/interviews", tags=["模拟面试"])
logger = logging.getLogger(__name__)
repository = InterviewRepository()


def _own_interview(db: Session, user: User, interview_id: int) -> Interview:
    interview = db.get(Interview, interview_id)
    if interview is None or interview.user_id != user.id:
        raise HTTPException(404, "面试不存在")
    return interview


def _build_out(
    interview: Interview,
    position: Position | None,
    interviewer: Interviewer | None,
    report: Report | None,
    message_count: int,
) -> InterviewOut:
    return InterviewOut(
        id=interview.id,
        position_id=interview.position_id,
        position_name=position.name if position else None,
        target_position=(interview.config or {}).get("target_position"),
        resume_id=interview.resume_id,
        interviewer_id=interview.interviewer_id,
        interviewer_name=interviewer.name if interviewer else None,
        difficulty=interview.difficulty,
        mode=interview.mode,
        interview_type=interview.interview_type,
        status=interview.status,
        max_rounds=interview.max_rounds,
        created_at=interview.created_at,
        report_id=report.id if report else None,
        overall_score=report.overall_score if report else None,
        message_count=message_count or 0,
        # 报告状态 pending（后台生成中）时前端展示"分析中"；ready/fallback/failed 均视为已有结果
        report_generating=bool(report and report.status == "pending"),
    )


def _make_out(db: Session, interview: Interview) -> InterviewOut:
    position = db.get(Position, interview.position_id) if interview.position_id else None
    interviewer = db.get(Interviewer, interview.interviewer_id) if interview.interviewer_id else None
    report = db.scalar(select(Report).where(Report.interview_id == interview.id))
    return _build_out(
        interview, position, interviewer, report, repository.message_count(db, interview.id)
    )


def _make_out_batch(db: Session, interviews: list[Interview]) -> list[InterviewOut]:
    """批量组装列表输出：预取岗位/面试官/报告/消息计数，避免 N+1。"""
    if not interviews:
        return []
    ids = [i.id for i in interviews]
    pos_ids = {i.position_id for i in interviews if i.position_id}
    iv_ids = {i.interviewer_id for i in interviews if i.interviewer_id}
    positions = (
        {p.id: p for p in db.scalars(select(Position).where(Position.id.in_(pos_ids))).all()}
        if pos_ids
        else {}
    )
    interviewers = (
        {iv.id: iv for iv in db.scalars(select(Interviewer).where(Interviewer.id.in_(iv_ids))).all()}
        if iv_ids
        else {}
    )
    reports = {
        r.interview_id: r
        for r in db.scalars(select(Report).where(Report.interview_id.in_(ids))).all()
    }
    counts = dict(
        db.execute(
            select(InterviewMessage.interview_id, func.count(InterviewMessage.id))
            .where(InterviewMessage.interview_id.in_(ids))
            .group_by(InterviewMessage.interview_id)
        ).all()
    )
    return [
        _build_out(
            i,
            positions.get(i.position_id),
            interviewers.get(i.interviewer_id),
            reports.get(i.id),
            counts.get(i.id, 0),
        )
        for i in interviews
    ]


@router.post("", response_model=InterviewOut, status_code=201)
@limiter.limit("20/minute")
def create_interview(
    request: Request,
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

    # ping=15：空闲时发送心跳注释，避免代理/网关超时掐断 SSE 长连接
    return EventSourceResponse(gen(), ping=15)


@router.post("/{interview_id}/start")
@limiter.limit("30/minute")
async def start_interview(
    request: Request,
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
        try:
            outcome = await orchestrator.start()
        except AppError as exc:
            yield {"event": "error", "data": json.dumps({"message": str(exc)}, ensure_ascii=False)}
            return
        except Exception as exc:  # noqa: BLE001 - SSE 兜底，避免开场失败直接断流
            logger.warning("面试开场失败 interview_id=%s: %s", interview_id, exc)
            yield {
                "event": "error",
                "data": json.dumps({"message": "面试官暂时不可用，请稍后重试"}, ensure_ascii=False),
            }
            return
        yield {
            "event": outcome["event"],
            "data": json.dumps(outcome["data"], ensure_ascii=False),
        }

    # ping=15：空闲时发送心跳注释，避免代理/网关超时掐断 SSE 长连接
    return EventSourceResponse(gen(), ping=15)


@router.post("/{interview_id}/answer")
@limiter.limit("30/minute")
async def submit_answer(
    request: Request,
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
            outcome = await orchestrator.answer(payload.content, request_id=payload.request_id)
        except AppError as exc:
            yield {"event": "error", "data": json.dumps({"message": str(exc)}, ensure_ascii=False)}
            return
        except Exception as exc:  # noqa: BLE001 - SSE 兜底，避免回答失败直接断流
            logger.warning("面试回答失败 interview_id=%s: %s", interview_id, exc)
            yield {
                "event": "error",
                "data": json.dumps({"message": "面试官暂时不可用，请稍后重试"}, ensure_ascii=False),
            }
            return
        # 面试结束时：先发面试官结束语，再发 finished
        farewell = (outcome.get("data") or {}).pop("farewell", None)
        if farewell:
            yield {"event": "farewell", "data": json.dumps({"message": farewell}, ensure_ascii=False)}
        yield {
            "event": outcome["event"],
            "data": json.dumps(outcome["data"], ensure_ascii=False),
        }

    # ping=15：空闲时发送心跳注释，避免代理/网关超时掐断 SSE 长连接
    return EventSourceResponse(gen(), ping=15)


@router.post("/{interview_id}/finish")
@limiter.limit("30/minute")
async def finish_interview(
    request: Request,
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
    rows = repository.list_by_user(db, user.id)
    return _make_out_batch(db, list(rows))


@router.get("/{interview_id}", response_model=InterviewDetailOut)
def interview_detail(
    interview_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """面试详情：完整问答流 + 复盘报告（用于历史复盘）。"""
    interview = _own_interview(db, user, interview_id)
    messages = repository.messages(db, interview.id)
    report = repository.report(db, interview.id)
    base = _make_out(db, interview)
    return InterviewDetailOut(
        **base.model_dump(),
        messages=[InterviewMessageOut.model_validate(m) for m in messages],
        report=report,
    )

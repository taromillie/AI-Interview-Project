"""真实面试复盘接口（Phase 3，FR-D-03）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.real_interview import RealInterview, RealInterviewItem
from app.models.user import User
from app.schemas.real_interview import (
    RealInterviewCreate,
    RealInterviewOut,
    RealInterviewSummaryOut,
)
from app.services.llm_utils import require_llm
from app.services.real_interview_review import review_real_interview

router = APIRouter(prefix="/real-interview", tags=["真实面试复盘"])


@router.post("", response_model=RealInterviewOut)
def create_real_interview(
    payload: RealInterviewCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """录入一次真实面试（含问答列表）。"""
    interview = RealInterview(
        user_id=user.id,
        company=payload.company,
        position=payload.position,
        interview_date=payload.interview_date,
        round_type=payload.round_type,
        notes=payload.notes,
    )
    db.add(interview)
    db.flush()
    for it in payload.items:
        db.add(
            RealInterviewItem(
                interview_id=interview.id,
                question=it.question,
                answer=it.answer,
            )
        )
    db.commit()
    db.refresh(interview)
    items = db.scalars(
        select(RealInterviewItem)
        .where(RealInterviewItem.interview_id == interview.id)
        .order_by(RealInterviewItem.id)
    ).all()
    return RealInterviewOut(
        **{c: getattr(interview, c) for c in
           ("id", "company", "position", "interview_date", "round_type", "notes", "review", "created_at")},
        items=[{"id": i.id, "question": i.question, "answer": i.answer, "score": i.score, "comment": i.comment} for i in items],
    )


@router.post("/{interview_id}/review", response_model=RealInterviewOut)
async def review_interview(
    interview_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """AI 逐题批改这次真实面试。"""
    interview = db.get(RealInterview, interview_id)
    if interview is None or interview.user_id != user.id:
        raise HTTPException(404, "面试记录不存在")
    llm = require_llm(db, user)
    await review_real_interview(db, llm, interview)
    items = db.scalars(
        select(RealInterviewItem)
        .where(RealInterviewItem.interview_id == interview.id)
        .order_by(RealInterviewItem.id)
    ).all()
    return RealInterviewOut(
        **{c: getattr(interview, c) for c in
           ("id", "company", "position", "interview_date", "round_type", "notes", "review", "created_at")},
        items=[{"id": i.id, "question": i.question, "answer": i.answer, "score": i.score, "comment": i.comment} for i in items],
    )


@router.get("", response_model=list[RealInterviewSummaryOut])
def list_real_interviews(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """真实面试记录列表。"""
    return db.scalars(
        select(RealInterview)
        .where(RealInterview.user_id == user.id)
        .order_by(RealInterview.id.desc())
        .limit(50)
    ).all()


@router.get("/{interview_id}", response_model=RealInterviewOut)
def get_real_interview(
    interview_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """真实面试详情（含问答与批改）。"""
    interview = db.get(RealInterview, interview_id)
    if interview is None or interview.user_id != user.id:
        raise HTTPException(404, "面试记录不存在")
    items = db.scalars(
        select(RealInterviewItem)
        .where(RealInterviewItem.interview_id == interview.id)
        .order_by(RealInterviewItem.id)
    ).all()
    return RealInterviewOut(
        **{c: getattr(interview, c) for c in
           ("id", "company", "position", "interview_date", "round_type", "notes", "review", "created_at")},
        items=[{"id": i.id, "question": i.question, "answer": i.answer, "score": i.score, "comment": i.comment} for i in items],
    )


@router.delete("/{interview_id}")
def delete_real_interview(
    interview_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除真实面试记录。"""
    interview = db.get(RealInterview, interview_id)
    if interview is None or interview.user_id != user.id:
        raise HTTPException(404, "面试记录不存在")
    db.query(RealInterviewItem).filter(RealInterviewItem.interview_id == interview.id).delete()
    db.delete(interview)
    db.commit()
    return {"ok": True}

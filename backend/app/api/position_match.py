"""简历→岗位智能匹配接口。"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.rate_limit import limiter
from app.models.position import Position
from app.models.resume import Resume, ResumePositionMatch
from app.models.user import User
from app.schemas.position_match import (
    MatchPositionsOut,
    MatchPositionsRequest,
    PositionMatchItem,
    PositionMatchOut,
)
from app.services.position_matcher import match_positions

router = APIRouter(prefix="/resumes", tags=["岗位匹配"])


def _get_owned_resume(db: Session, user: User, resume_id: int) -> Resume:
    resume = db.get(Resume, resume_id)
    if resume is None or resume.user_id != user.id:
        raise HTTPException(404, "简历不存在")
    return resume


def _to_item(r: dict) -> PositionMatchItem:
    p: Position = r["position"]
    return PositionMatchItem(
        position_id=p.id,
        name=p.name,
        direction=p.direction,
        difficulty=p.difficulty,
        skills=p.skills or [],
        company=p.company or "",
        city=p.city or "",
        salary_min=p.salary_min,
        salary_max=p.salary_max,
        description=p.description or "",
        match_score=r["match_score"],
        matched_skills=r["matched_skills"],
        missing_skills=r["missing_skills"],
        reason=r["reason"],
        dimension_breakdown=r["dimension_breakdown"],
    )


@router.post("/{resume_id}/match-positions", response_model=MatchPositionsOut)
@limiter.limit("20/minute")
async def run_match_positions(
    request: Request,
    resume_id: int,
    payload: MatchPositionsRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """根据简历技能从岗位库中匹配 Top N 推荐岗位，并覆盖保存为该简历的最新推荐结果。"""
    resume = _get_owned_resume(db, user, resume_id)
    items = match_positions(
        db,
        resume,
        limit=payload.limit,
        direction=payload.direction,
        city=payload.city,
        difficulty=payload.difficulty,
    )

    # 覆盖式保存：同一简历只保留最近一次匹配结果
    db.execute(delete(ResumePositionMatch).where(ResumePositionMatch.resume_id == resume_id))
    for r in items:
        db.add(
            ResumePositionMatch(
                user_id=user.id,
                resume_id=resume_id,
                position_id=r["position"].id,
                match_score=r["match_score"],
                matched_skills=r["matched_skills"],
                missing_skills=r["missing_skills"],
                reason=r["reason"],
            )
        )
    db.commit()

    return MatchPositionsOut(
        resume_id=resume_id,
        resume_name=resume.name,
        matched_at=datetime.now(),
        results=[_to_item(r) for r in items],
    )


@router.get("/{resume_id}/matches", response_model=list[PositionMatchOut])
def list_resume_matches(
    resume_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """该简历最近一次的匹配推荐记录（带岗位快照，按创建时间倒序）。"""
    _get_owned_resume(db, user, resume_id)
    records = db.scalars(
        select(ResumePositionMatch)
        .where(ResumePositionMatch.resume_id == resume_id)
        .order_by(ResumePositionMatch.id.desc())
    ).all()
    out: list[PositionMatchOut] = []
    for rec in records:
        p = db.get(Position, rec.position_id)
        out.append(
            PositionMatchOut(
                id=rec.id,
                position_id=rec.position_id,
                position_name=p.name if p else "",
                company=p.company if p else "",
                city=p.city if p else "",
                salary_min=p.salary_min if p else None,
                salary_max=p.salary_max if p else None,
                direction=p.direction if p else "",
                difficulty=p.difficulty if p else "",
                skills=p.skills if p else [],
                match_score=rec.match_score,
                matched_skills=rec.matched_skills,
                missing_skills=rec.missing_skills,
                reason=rec.reason,
                created_at=rec.created_at,
            )
        )
    return out


@router.delete("/{resume_id}/matches")
def clear_resume_matches(
    resume_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """清空该简历的匹配推荐记录。"""
    _get_owned_resume(db, user, resume_id)
    db.execute(delete(ResumePositionMatch).where(ResumePositionMatch.resume_id == resume_id))
    db.commit()
    return {"status": "cleared"}

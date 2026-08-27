"""转行诊断接口（Phase 2）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.career import CareerPlan
from app.models.resume import Resume
from app.models.user import User
from app.schemas.career import CareerDiagnosisOut, CareerDiagnosisRequest, CareerPlanOut
from app.services.career_diagnosis import run_career_diagnosis
from app.services.llm_utils import require_llm

router = APIRouter(prefix="/career", tags=["转行诊断"])


@router.post("/diagnosis", response_model=CareerDiagnosisOut)
async def career_diagnosis(
    payload: CareerDiagnosisRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """转行诊断：当前岗位 → 目标岗位，输出可迁移技能/缺口/学习路径。"""
    resume = None
    if payload.resume_id is not None:
        resume = db.get(Resume, payload.resume_id)
        if resume is None or resume.user_id != user.id:
            raise HTTPException(404, "指定的简历不存在")

    llm = require_llm(db, user)
    plan = await run_career_diagnosis(
        db,
        llm,
        user_id=user.id,
        from_position=payload.from_position,
        to_position=payload.to_position,
        resume=resume,
    )
    return CareerDiagnosisOut(
        id=plan.id,
        transferable=plan.transferable,
        gaps=plan.gaps,
        roadmap=plan.roadmap,
        summary=plan.summary,
    )


@router.get("/plans", response_model=list[CareerPlanOut])
def list_plans(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """转行诊断历史记录。"""
    return db.scalars(
        select(CareerPlan)
        .where(CareerPlan.user_id == user.id)
        .order_by(CareerPlan.id.desc())
        .limit(20)
    ).all()

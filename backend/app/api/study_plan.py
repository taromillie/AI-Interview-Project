"""备战日历接口（Phase 3，FR-B-06）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.resume import Resume
from app.models.study import StudyPlan
from app.models.user import User
from app.schemas.study_plan import (
    StudyPlanGenerateRequest,
    StudyPlanOut,
    StudyPlanTaskIn,
)
from app.services.llm_utils import require_llm
from app.services.study_plan import generate_study_plan

router = APIRouter(prefix="/study-plan", tags=["备战日历"])


@router.post("/generate", response_model=StudyPlanOut)
async def create_study_plan(
    payload: StudyPlanGenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """生成冲刺备战计划（基于能力画像缺口 + 目标岗位）。"""
    resume = None
    if payload.resume_id is not None and payload.resume_id >= 0:
        if payload.resume_id > 0:
            resume = db.get(Resume, payload.resume_id)
            if resume is None or resume.user_id != user.id:
                raise HTTPException(404, "指定的简历不存在")
        else:  # 0 = 最近一份
            resume = db.scalar(
                select(Resume).where(Resume.user_id == user.id).order_by(Resume.id.desc())
            )
    llm = require_llm(db, user)
    plan = await generate_study_plan(
        db, llm, user_id=user.id, target_position=payload.target_position,
        days=payload.days, resume=resume,
    )
    return plan


@router.get("/plans", response_model=list[StudyPlanOut])
def list_plans(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """备战计划历史。"""
    return db.scalars(
        select(StudyPlan)
        .where(StudyPlan.user_id == user.id)
        .order_by(StudyPlan.id.desc())
        .limit(20)
    ).all()


@router.patch("/{plan_id}", response_model=StudyPlanOut)
def update_plan(
    plan_id: int,
    payload: StudyPlanTaskIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """勾选/取消勾选某天任务；全部完成后状态置为 completed。"""
    plan = db.get(StudyPlan, plan_id)
    if plan is None or plan.user_id != user.id:
        raise HTTPException(404, "计划不存在")
    tasks = plan.tasks or []
    updated = False
    for t in tasks:
        if int(t.get("day", 0)) == payload.day:
            t["done"] = bool(payload.done)
            updated = True
            break
    if not updated and payload.done:
        tasks.append({"day": payload.day, "done": True, "title": "", "description": "", "topics": []})
    plan.tasks = tasks
    if tasks and all(t.get("done") for t in tasks):
        plan.status = "completed"
    else:
        plan.status = "active"
    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/{plan_id}")
def delete_plan(
    plan_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除备战计划。"""
    plan = db.get(StudyPlan, plan_id)
    if plan is None or plan.user_id != user.id:
        raise HTTPException(404, "计划不存在")
    db.delete(plan)
    db.commit()
    return {"ok": True}

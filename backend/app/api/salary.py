"""谈薪评估接口（Phase 2）。"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.rate_limit import limiter
from app.models.career import SalaryEval
from app.models.resume import Resume
from app.models.user import User
from app.schemas.career import SalaryEvalHistoryOut, SalaryEvalOut, SalaryEvalRequest
from app.services.llm_utils import require_llm
from app.services.salary_eval import run_salary_eval

router = APIRouter(prefix="/salary", tags=["谈薪评估"])


@router.post("/evaluate", response_model=SalaryEvalOut)
@limiter.limit("20/minute")
async def evaluate_salary(
    request: Request,
    payload: SalaryEvalRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """谈薪评估：技能栈 + 年限 + 城市 → 薪资区间与谈薪策略（可结合简历）。"""
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
    ev = await run_salary_eval(
        db,
        llm,
        user_id=user.id,
        payload=payload,
        resume=resume,
    )
    return SalaryEvalOut(
        id=ev.id,
        salary_range=ev.result["salary_range"],
        factors=ev.result["factors"],
        strategy=ev.result["strategy"],
    )


@router.get("/evals", response_model=list[SalaryEvalHistoryOut])
def list_evals(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """谈薪评估历史记录。"""
    return db.scalars(
        select(SalaryEval)
        .where(SalaryEval.user_id == user.id)
        .order_by(SalaryEval.id.desc())
        .limit(20)
    ).all()

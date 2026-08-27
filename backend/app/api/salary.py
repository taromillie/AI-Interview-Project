"""谈薪评估接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.career import SalaryEvalOut, SalaryEvalRequest

router = APIRouter(prefix="/salary", tags=["谈薪评估"])


@router.post("/evaluate", response_model=SalaryEvalOut)
def evaluate_salary(
    payload: SalaryEvalRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # TODO(Phase 2): 接入谈薪评估服务
    raise NotImplementedError("谈薪评估服务将在下一阶段实现")

"""转行诊断接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.career import CareerDiagnosisOut, CareerDiagnosisRequest

router = APIRouter(prefix="/career", tags=["转行诊断"])


@router.post("/diagnosis", response_model=CareerDiagnosisOut)
def career_diagnosis(
    payload: CareerDiagnosisRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # TODO(Phase 2): 接入转行诊断服务
    raise NotImplementedError("转行诊断服务将在下一阶段实现")

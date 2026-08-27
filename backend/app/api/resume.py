"""简历上传与简历×JD 匹配诊断接口。"""
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.diagnostic import ResumeDiagnosticOut, ResumeDiagnosticRequest, ResumeOut

router = APIRouter(prefix="/resumes", tags=["简历诊断"])


@router.post("/upload", response_model=ResumeOut)
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # TODO(Phase 2): 接入简历解析服务（PyMuPDF + LLM 结构化提取）
    raise NotImplementedError("简历解析服务将在下一阶段实现")


@router.post("/diagnose", response_model=ResumeDiagnosticOut)
def diagnose(
    payload: ResumeDiagnosticRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # TODO(Phase 2): 接入简历×JD 匹配服务
    raise NotImplementedError("简历×JD 匹配服务将在下一阶段实现")

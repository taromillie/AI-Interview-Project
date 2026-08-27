"""简历上传与简历×JD 匹配诊断接口（Phase 1）。"""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.resume import JobDescription, MatchDiagnostic, Resume
from app.models.user import User
from app.schemas.diagnostic import ResumeDiagnosticOut, ResumeDiagnosticRequest, ResumeOut
from app.services.llm_utils import require_llm
from app.services.resume_matcher import run_diagnostic
from app.services.resume_parser import extract_text_from_bytes, parse_resume

router = APIRouter(prefix="/resumes", tags=["简历诊断"])

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


def _auto_name(parsed: dict) -> str:
    """从解析画像自动生成简历名称：姓名 · 目标岗位，逐级兜底。"""
    basic = parsed.get("basic") or {}
    name = str(basic.get("name") or "").strip()
    pos = str(basic.get("target_position") or "").strip()
    if name and pos:
        return f"{name} · {pos}"
    if name:
        return f"{name} 的简历"
    if pos:
        return f"求职简历（{pos}）"
    return "我的简历"


@router.post("/upload", response_model=ResumeOut)
async def upload_resume(
    file: UploadFile | None = File(default=None),
    raw_text: str | None = Form(default=None),
    name: str | None = Form(default=None, description="自定义简历名称，留空自动命名"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传简历（PDF/TXT 文件或粘贴文本），解析后保存。"""
    if file is None and not (raw_text and raw_text.strip()):
        raise HTTPException(400, "请上传 PDF/TXT 简历文件，或粘贴简历文本")

    if file is not None:
        data = await file.read()
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(413, "文件大小不能超过 2MB")
        text = extract_text_from_bytes(data, file.filename or "")
        if not text or not text.strip():
            raise HTTPException(422, "无法从该文件中提取到文本，请尝试粘贴文本")
    else:
        text = raw_text

    llm = require_llm(db, user)
    parsed = await parse_resume(llm, text)
    custom_name = (name or "").strip()
    resume = Resume(
        user_id=user.id,
        name=custom_name or _auto_name(parsed),
        raw_text=text,
        parsed_json=parsed,
        skills=parsed["skills"],
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.delete("/{resume_id}")
def delete_resume(
    resume_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除简历，同时级联删除其匹配诊断记录。"""
    resume = db.get(Resume, resume_id)
    if resume is None or resume.user_id != user.id:
        raise HTTPException(404, "简历不存在")
    db.execute(delete(MatchDiagnostic).where(MatchDiagnostic.resume_id == resume_id))
    db.delete(resume)
    db.commit()
    return {"status": "deleted"}


@router.post("/diagnose", response_model=ResumeDiagnosticOut)
async def diagnose(
    payload: ResumeDiagnosticRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """对指定简历与 JD 执行简历×JD 匹配诊断（缺省取最近一份/直接传文本）。"""
    if payload.resume_id is not None:
        resume = db.get(Resume, payload.resume_id)
        if resume is None or resume.user_id != user.id:
            raise HTTPException(404, "指定的简历不存在")
    else:
        resume = db.scalar(
            select(Resume)
            .where(Resume.user_id == user.id)
            .order_by(Resume.id.desc())
        )
    if resume is None:
        raise HTTPException(400, "请先上传简历，再执行匹配诊断")

    if payload.jd_id is not None:
        jd = db.get(JobDescription, payload.jd_id)
        if jd is None or jd.user_id != user.id:
            raise HTTPException(404, "指定的 JD 不存在")
        jd_text = jd.content
    else:
        jd_text = payload.jd_text

    if not jd_text or len(jd_text.strip()) < 20:
        raise HTTPException(422, "JD 内容至少 20 字")

    llm = require_llm(db, user)
    diagnostic = await run_diagnostic(db, llm, resume, jd_text)
    return ResumeDiagnosticOut(
        diagnostic_id=diagnostic.id,
        match_score=diagnostic.match_score,
        gaps=diagnostic.gaps,
        resume_suggestions=diagnostic.suggestions,
    )


@router.get("", response_model=list[ResumeOut])
def list_resumes(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Resume)
        .where(Resume.user_id == user.id)
        .order_by(Resume.id.desc())
        .limit(20)
    ).all()


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(
    resume_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = db.get(Resume, resume_id)
    if resume is None or resume.user_id != user.id:
        raise HTTPException(404, "简历不存在")
    return resume


@router.put("/{resume_id}", response_model=ResumeOut)
async def update_resume(
    resume_id: int,
    file: UploadFile | None = File(default=None),
    raw_text: str | None = Form(default=None),
    name: str | None = Form(default=None, description="自定义简历名称，留空则按解析结果自动命名"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新历史简历（支持粘贴文本或重新上传文件，重新解析画像）。"""
    resume = db.get(Resume, resume_id)
    if resume is None or resume.user_id != user.id:
        raise HTTPException(404, "简历不存在")

    if file is None and not (raw_text and raw_text.strip()):
        raise HTTPException(400, "请上传 PDF/TXT 简历文件，或粘贴简历文本")

    if file is not None:
        data = await file.read()
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(413, "文件大小不能超过 2MB")
        text = extract_text_from_bytes(data, file.filename or "")
        if not text or not text.strip():
            raise HTTPException(422, "无法从该文件中提取到文本，请尝试粘贴文本")
    else:
        text = raw_text

    custom_name = (name or "").strip()
    # 内容未变化（如仅修改名称）：跳过 LLM 解析，秒级返回
    if file is None and text == (resume.raw_text or ""):
        if custom_name:
            resume.name = custom_name
        db.commit()
        db.refresh(resume)
        return resume

    llm = require_llm(db, user)
    parsed = await parse_resume(llm, text)
    resume.raw_text = text
    resume.file_path = None
    resume.parsed_json = parsed
    resume.skills = parsed["skills"]
    if custom_name:
        resume.name = custom_name
    elif not resume.name:
        resume.name = _auto_name(parsed)
    db.commit()
    db.refresh(resume)
    return resume

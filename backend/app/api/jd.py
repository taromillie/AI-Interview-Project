"""岗位 JD 历史管理。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.resume import JobDescription
from app.models.user import User
from app.schemas.diagnostic import JDOut, JDRequest

router = APIRouter(prefix="/jds", tags=["JD 管理"])


@router.get("", response_model=list[JDOut])
def list_jds(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(JobDescription)
        .where(JobDescription.user_id == user.id)
        .order_by(JobDescription.id.desc())
    ).all()
    return rows


@router.post("", response_model=JDOut, status_code=201)
def create_jd(
    payload: JDRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jd = JobDescription(user_id=user.id, title=payload.title, content=payload.content)
    db.add(jd)
    db.commit()
    db.refresh(jd)
    return jd


@router.put("/{jd_id}", response_model=JDOut)
def update_jd(
    jd_id: int,
    payload: JDRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jd = db.get(JobDescription, jd_id)
    if jd is None or jd.user_id != user.id:
        raise HTTPException(404, "JD 不存在")
    jd.title = payload.title
    jd.content = payload.content
    db.commit()
    db.refresh(jd)
    return jd


@router.delete("/{jd_id}", status_code=204)
def delete_jd(
    jd_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jd = db.get(JobDescription, jd_id)
    if jd is None or jd.user_id != user.id:
        raise HTTPException(404, "JD 不存在")
    db.delete(jd)
    db.commit()

"""岗位收藏与投递跟踪接口（P2，FR-C-01 增强）。

职责：
- 收藏：POST/DELETE /positions/{id}/favorite
- 投递状态：PUT/DELETE /positions/{id}/application（saved/applied/interviewing/offer/rejected）
- 概览：GET /summary 一次性返回当前用户收藏 id 集合与投递状态映射，供前端本地匹配
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.job_track import JobApplication, JobFavorite
from app.models.position import Position
from app.models.user import User

router = APIRouter(prefix="/job-track", tags=["岗位跟踪"])

APPLICATION_STATUS = {"saved", "applied", "interviewing", "offer", "rejected"}


def _ensure_position(db: Session, position_id: int) -> None:
    if db.get(Position, position_id) is None:
        raise HTTPException(status_code=404, detail="岗位不存在")


def _to_application_dict(app: JobApplication) -> dict:
    return {
        "position_id": app.position_id,
        "status": app.status,
        "note": app.note,
        "updated_at": app.updated_at.isoformat() if app.updated_at else None,
    }


@router.get("/summary")
def get_track_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """当前用户收藏与投递概览。"""
    favorite_ids = db.scalars(
        select(JobFavorite.position_id).where(JobFavorite.user_id == user.id)
    ).all()
    applications = db.scalars(
        select(JobApplication).where(JobApplication.user_id == user.id)
    ).all()
    return {
        "favorite_ids": list(favorite_ids),
        "applications": {a.position_id: _to_application_dict(a) for a in applications},
    }


@router.post("/positions/{position_id}/favorite")
def favorite_position(
    position_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """收藏岗位（幂等）。"""
    _ensure_position(db, position_id)
    exists = db.scalar(
        select(JobFavorite).where(
            JobFavorite.user_id == user.id,
            JobFavorite.position_id == position_id,
        )
    )
    if exists is None:
        db.add(JobFavorite(user_id=user.id, position_id=position_id))
        db.commit()
    return {"ok": True, "favorite": True}


@router.delete("/positions/{position_id}/favorite")
def unfavorite_position(
    position_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """取消收藏（幂等）。"""
    db.execute(
        delete(JobFavorite).where(
            JobFavorite.user_id == user.id,
            JobFavorite.position_id == position_id,
        )
    )
    db.commit()
    return {"ok": True, "favorite": False}


@router.put("/positions/{position_id}/application")
def set_application(
    position_id: int,
    status: str = Query(...),
    note: str = Query("", max_length=300),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """设置 / 更新投递状态（幂等 upsert）。"""
    if status not in APPLICATION_STATUS:
        raise HTTPException(status_code=422, detail="非法的投递状态")
    _ensure_position(db, position_id)
    app = db.scalar(
        select(JobApplication).where(
            JobApplication.user_id == user.id,
            JobApplication.position_id == position_id,
        )
    )
    if app is None:
        app = JobApplication(user_id=user.id, position_id=position_id)
        db.add(app)
    app.status = status
    app.note = note
    db.commit()
    db.refresh(app)
    return {"ok": True, "application": _to_application_dict(app)}


@router.delete("/positions/{position_id}/application")
def remove_application(
    position_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """移除投递跟踪（幂等）。"""
    db.execute(
        delete(JobApplication).where(
            JobApplication.user_id == user.id,
            JobApplication.position_id == position_id,
        )
    )
    db.commit()
    return {"ok": True}

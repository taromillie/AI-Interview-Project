"""能力画像接口（Phase 2）。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.career import ProfileOut
from app.services.ability_profile import aggregate_ability_profile

router = APIRouter(prefix="/profile", tags=["能力画像"])


@router.get("", response_model=ProfileOut)
def get_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """多场面试复盘报告聚合出的能力画像（雷达图数据源）。"""
    profile = aggregate_ability_profile(db, user.id)
    if profile is None:
        return ProfileOut()
    return ProfileOut(
        dimensions=profile["dimensions"],
        skill_scores=profile["skill_scores"],
        weak_points=profile["weak_points"],
        strengths=profile["strengths"],
        suggestions=profile["suggestions"],
        trend=profile["trend"],
        report_count=profile["report_count"],
        updated_at=profile["updated_at"],
    )

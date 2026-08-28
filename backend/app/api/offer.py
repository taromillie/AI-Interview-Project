"""Offer 对比接口（Phase 3，FR-F-03）。"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.rate_limit import limiter
from app.models.offer import Offer
from app.models.user import User
from app.schemas.offer import OfferCompareOut, OfferCreate, OfferOut
from app.services.llm_utils import require_llm
from app.services.offer_compare import compare_offers

router = APIRouter(prefix="/offers", tags=["Offer 对比"])


@router.post("", response_model=OfferOut)
def create_offer(
    payload: OfferCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """新增一个 Offer。"""
    offer = Offer(user_id=user.id, **payload.model_dump())
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


@router.get("", response_model=list[OfferOut])
def list_offers(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """我的 Offer 列表。"""
    return db.scalars(
        select(Offer).where(Offer.user_id == user.id).order_by(Offer.id.desc())
    ).all()


@router.put("/{offer_id}", response_model=OfferOut)
def update_offer(
    offer_id: int,
    payload: OfferCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新 Offer。"""
    offer = db.get(Offer, offer_id)
    if offer is None or offer.user_id != user.id:
        raise HTTPException(404, "Offer 不存在")
    for k, v in payload.model_dump().items():
        setattr(offer, k, v)
    db.commit()
    db.refresh(offer)
    return offer


@router.delete("/{offer_id}")
def delete_offer(
    offer_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除 Offer。"""
    offer = db.get(Offer, offer_id)
    if offer is None or offer.user_id != user.id:
        raise HTTPException(404, "Offer 不存在")
    db.delete(offer)
    db.commit()
    return {"ok": True}


@router.post("/compare", response_model=OfferCompareOut)
@limiter.limit("20/minute")
async def compare(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """对比我全部 Offer：结构化表格 + AI 建议。"""
    offers = db.scalars(
        select(Offer).where(Offer.user_id == user.id).order_by(Offer.id.asc())
    ).all()
    if len(offers) < 2:
        raise HTTPException(400, "至少需要 2 个 Offer 才能对比")
    llm = require_llm(db, user)
    table, analysis = await compare_offers(llm, offers)
    return OfferCompareOut(table=table, analysis=analysis)

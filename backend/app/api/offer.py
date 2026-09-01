"""Offer 对比接口（Phase 3，FR-F-03）。"""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.rate_limit import limiter
from app.models.offer import Offer, OfferCompareRecord
from app.models.user import User
from app.schemas.offer import (
    OfferCompareIn,
    OfferCompareOut,
    OfferCompareRecordDetailOut,
    OfferCompareRecordOut,
    OfferCreate,
    OfferOut,
)
from app.services.llm_utils import require_llm
from app.services.offer_compare import (
    _rule_analysis,
    build_compare_table,
    stream_compare_analysis,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/offers", tags=["Offer 对比"])


def _find_cached_record(db: Session, user_id: int, offer_ids: list[int]) -> OfferCompareRecord | None:
    """查找最近一条相同 Offer 组合的完整快照（analysis 已生成）。"""
    target = set(offer_ids)
    rows = db.scalars(
        select(OfferCompareRecord)
        .where(OfferCompareRecord.user_id == user_id)
        .order_by(OfferCompareRecord.id.desc())
        .limit(50)
    ).all()
    for r in rows:
        try:
            ids = set(json.loads(r.offer_ids or "[]"))
        except json.JSONDecodeError:
            continue
        if ids == target and r.analysis:
            return r
    return None


def _sse_event(text: str) -> str:
    return f"data: {json.dumps({'chunk': text}, ensure_ascii=False)}\n\n"


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
    payload: OfferCompareIn | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """对比指定（或全部）Offer：表格秒回，AI 分析经 SSE 流式补全；同组合缓存命中则直接复用。"""
    stmt = select(Offer).where(Offer.user_id == user.id)
    if payload and payload.offer_ids:
        stmt = stmt.where(Offer.id.in_(payload.offer_ids))
    offers = db.scalars(stmt.order_by(Offer.id.asc())).all()
    if len(offers) < 2:
        raise HTTPException(400, "至少需要 2 个 Offer 才能对比")
    offer_ids = [o.id for o in offers]
    # 同组合缓存：最近一次相同 Offer 组合的完整快照直接复用，秒回
    cached = _find_cached_record(db, user.id, offer_ids)
    if cached is not None:
        try:
            table = json.loads(cached.table_json or "[]")
        except json.JSONDecodeError:
            table = []
        return OfferCompareOut(table=table, analysis=cached.analysis, record_id=cached.id)
    # 未命中：先建记录返回表格，AI 分析由 /compare/history/{id}/stream 流式补全
    require_llm(db, user)
    table = build_compare_table(offers)
    record = OfferCompareRecord(
        user_id=user.id,
        offer_ids=json.dumps(offer_ids, ensure_ascii=False),
        company_names=" vs ".join(o.company for o in offers),
        table_json=json.dumps(table, ensure_ascii=False),
        analysis="",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return OfferCompareOut(table=table, analysis="", record_id=record.id)


@router.get("/compare/history", response_model=list[OfferCompareRecordOut])
def list_compare_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    """我的对比历史列表（按时间倒序）。"""
    return db.scalars(
        select(OfferCompareRecord)
        .where(OfferCompareRecord.user_id == user.id)
        .order_by(OfferCompareRecord.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()


@router.get("/compare/history/{record_id}", response_model=OfferCompareRecordDetailOut)
def get_compare_history(
    record_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """对比历史详情（回看快照）。"""
    record = db.get(OfferCompareRecord, record_id)
    if record is None or record.user_id != user.id:
        raise HTTPException(404, "记录不存在")
    try:
        table = json.loads(record.table_json or "[]")
        offer_ids = json.loads(record.offer_ids or "[]")
    except json.JSONDecodeError:
        table, offer_ids = [], []
    return OfferCompareRecordDetailOut(
        id=record.id,
        company_names=record.company_names,
        offer_ids=offer_ids,
        table=table,
        analysis=record.analysis,
        created_at=record.created_at,
    )


@router.delete("/compare/history/{record_id}")
def delete_compare_history(
    record_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除一条对比历史。"""
    record = db.get(OfferCompareRecord, record_id)
    if record is None or record.user_id != user.id:
        raise HTTPException(404, "记录不存在")
    db.delete(record)
    db.commit()
    return {"ok": True}


@router.get("/compare/history/{record_id}/stream")
async def stream_compare_history(
    record_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """SSE 流式补全一条对比记录的 AI 分析（边生成边推送，前端打字机显示）。

    - 记录已有 analysis：一次性下发（同组合缓存 / 已完成的分析）
    - 记录为空：调用 LLM 流式生成并写入记录；失败时规则兜底
    """
    record = db.get(OfferCompareRecord, record_id)
    if record is None or record.user_id != user.id:
        raise HTTPException(404, "记录不存在")

    if record.analysis:
        async def done():
            yield _sse_event(record.analysis)

        return StreamingResponse(done(), media_type="text/event-stream")

    try:
        offer_ids = json.loads(record.offer_ids or "[]")
    except json.JSONDecodeError:
        offer_ids = []
    offers = db.scalars(
        select(Offer).where(Offer.id.in_(offer_ids)).order_by(Offer.id.asc())
    ).all()
    if len(offers) < 2:
        async def missing():
            yield _sse_event("部分 Offer 已被删除，无法重新生成分析，请重新添加后再次对比。")

        return StreamingResponse(missing(), media_type="text/event-stream")

    llm = require_llm(db, user)

    async def gen():
        collected: list[str] = []
        try:
            try:
                async for chunk in stream_compare_analysis(llm, offers):
                    collected.append(chunk)
                    yield _sse_event(chunk)
            except Exception as exc:  # noqa: BLE001 - 流中断时通知前端，规则兜底仍在 finally 执行
                logger.warning("Offer 对比分析流式生成失败 record_id=%s: %s", record_id, exc)
                yield (
                    "event: error\ndata: "
                    + json.dumps({"message": "AI 分析中断，已切换为本地摘要"}, ensure_ascii=False)
                    + "\n\n"
                )
        finally:
            text = "".join(collected).strip()
            if not text:
                text = _rule_analysis(offers)
            if text:
                record.analysis = text[:2000]
                db.commit()

    return StreamingResponse(gen(), media_type="text/event-stream")

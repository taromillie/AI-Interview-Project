"""LLM Provider 配置接口。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.security import decrypt_api_key, encrypt_api_key
from app.llm.factory import KNOWN_BASE_URLS
from app.models.user import LlmProvider, User
from app.schemas.auth import ProviderConfigOut, ProviderConfigRequest

router = APIRouter(prefix="/providers", tags=["模型配置"])


@router.get("", response_model=list[ProviderConfigOut])
def list_providers(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(LlmProvider).where(LlmProvider.user_id == user.id)).all()
    return rows


@router.post("", response_model=ProviderConfigOut, status_code=201)
def upsert_provider(
    payload: ProviderConfigRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    name = payload.provider_name.lower().strip()
    if name not in KNOWN_BASE_URLS and (not payload.base_url or not payload.model):
        raise HTTPException(
            status_code=400,
            detail=f"未知 Provider '{name}'，请提供 base_url 与 model",
        )
    row = db.scalar(
        select(LlmProvider).where(
            LlmProvider.user_id == user.id,
            LlmProvider.provider_name == name,
        )
    )
    if row is None:
        row = LlmProvider(user_id=user.id, provider_name=name)
        db.add(row)
    row.api_key_encrypted = encrypt_api_key(payload.api_key)
    row.base_url = payload.base_url or KNOWN_BASE_URLS.get(name)
    row.model = payload.model
    row.is_active = True
    # 同一用户仅一个活跃 Provider
    for other in db.scalars(
        select(LlmProvider).where(LlmProvider.user_id == user.id)
    ).all():
        other.is_active = other.id == row.id
    db.commit()
    db.refresh(row)
    return row


@router.get("/active")
def get_active_provider(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.scalar(
        select(LlmProvider).where(
            LlmProvider.user_id == user.id,
            LlmProvider.is_active.is_(True),
        )
    )
    if row is None:
        return {"configured": False}
    return {
        "configured": True,
        "provider_name": row.provider_name,
        "base_url": row.base_url,
        "model": row.model,
        "api_key_preview": decrypt_api_key(row.api_key_encrypted)[:6] + "****",
    }

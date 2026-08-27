"""LLM 实例获取工具：按用户配置的活跃 Provider 创建实例。"""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decrypt_api_key
from app.llm.base import LLMProvider
from app.llm.factory import get_llm
from app.models.user import LlmProvider, User


def get_llm_for_user(db: Session, user_id: int) -> LLMProvider | None:
    """获取用户配置的活跃 LLM 实例；未配置返回 None。"""
    row = db.scalar(
        select(LlmProvider).where(
            LlmProvider.user_id == user_id,
            LlmProvider.is_active.is_(True),
        )
    )
    if row is None:
        return None
    return get_llm(
        provider_name=row.provider_name,
        api_key=decrypt_api_key(row.api_key_encrypted),
        base_url=row.base_url,
        model=row.model,
    )


def require_llm(db: Session, user: User) -> LLMProvider:
    """获取 LLM，未配置时抛出 400 提示先到「模型配置」页完成设置。"""
    llm = get_llm_for_user(db, user.id)
    if llm is None:
        raise HTTPException(
            status_code=400,
            detail="尚未配置 LLM API，请先在「模型配置」页填写 API Key 并设为当前模型",
        )
    return llm

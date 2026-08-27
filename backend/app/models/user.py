"""用户与 LLM Provider 配置。"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    email: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="user")  # user / admin
    target_city: Mapped[str | None] = mapped_column(String(50), nullable=True)
    years_of_exp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_position: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    providers: Mapped[list["LlmProvider"]] = relationship(back_populates="user")


class LlmProvider(Base):
    __tablename__ = "llm_providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    provider_name: Mapped[str] = mapped_column(String(30))  # deepseek/kimi/glm/qwen/openai...
    api_key_encrypted: Mapped[str] = mapped_column(String(512))
    base_url: Mapped[str | None] = mapped_column(String(200), nullable=True)
    model: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="providers")

"""面试官角色模型（角色库，人设+风格+难度偏移）。"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Interviewer(Base):
    __tablename__ = "interviewers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))                     # 角色名，如「CTO 技术面」
    title: Mapped[str] = mapped_column(String(80), default="")        # 角色标签/职务描述
    persona: Mapped[str] = mapped_column(Text, default="")            # 人设描述（注入 system prompt）
    style: Mapped[str] = mapped_column(Text, default="")              # 提问风格要点（注入 prompt）
    interview_type: Mapped[str] = mapped_column(String(20), default="all")
    # all / normal / switch / salary：适用的面试模式
    difficulty_bias: Mapped[int] = mapped_column(Integer, default=0)
    # 难度偏移：-1 偏易 / 0 标准 / +1 偏难，叠加用户所选难度
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)    # 内置公开角色（ADMIN 维护）
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

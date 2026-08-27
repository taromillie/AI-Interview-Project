"""备战日历（Phase 3）：冲刺备战计划。"""
from datetime import datetime

from sqlalchemy import DateTime, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class StudyPlan(Base):
    """一次冲刺备战计划（N 天，每天一组学习任务）。

    tasks 结构：[{day, title, description, topics, done}]
    """

    __tablename__ = "study_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(String(120), default="冲刺备战计划")
    target_position: Mapped[str] = mapped_column(String(80), default="")
    days: Mapped[int] = mapped_column(default=14)
    tasks: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active/completed/archived
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

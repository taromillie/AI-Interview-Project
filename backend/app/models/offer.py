"""Offer 管理（Phase 3）：多 offer 录入与对比。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Offer(Base):
    """一个工作 Offer。"""

    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    company: Mapped[str] = mapped_column(String(80))
    position: Mapped[str] = mapped_column(String(80), default="")
    city: Mapped[str] = mapped_column(String(50), default="")
    monthly_salary: Mapped[int] = mapped_column(default=0)      # 月薪（元）
    bonus_months: Mapped[int] = mapped_column(default=0)        # 年终奖月数
    stock_value: Mapped[int] = mapped_column(default=0)         # 股票/期权年化估值（元/年）
    work_balance: Mapped[int] = mapped_column(default=0)        # 工作生活平衡评分 1-10
    benefits: Mapped[str] = mapped_column(Text, default="")     # 福利（公积金、餐补等）
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

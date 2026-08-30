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


class OfferCompareRecord(Base):
    """一次 Offer 对比的历史记录。

    保存快照（offer_ids / 公司名 / 对比表 / AI 建议），即使之后删除 Offer，
    历史记录仍可完整回看。
    """

    __tablename__ = "offer_compare_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    offer_ids: Mapped[str] = mapped_column(Text, default="")  # JSON 数组快照
    company_names: Mapped[str] = mapped_column(String(255), default="")  # 如 "腾讯 vs 阿里"
    table_json: Mapped[str] = mapped_column(Text, default="")  # 对比表 JSON 快照
    analysis: Mapped[str] = mapped_column(Text, default="")  # AI 综合建议快照
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

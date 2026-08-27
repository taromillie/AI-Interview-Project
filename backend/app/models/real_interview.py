"""真实面试复盘（Phase 3）：录入真实面试问答，AI 逐题批改。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class RealInterview(Base):
    """一次真实面试记录。"""

    __tablename__ = "real_interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    company: Mapped[str] = mapped_column(String(80))
    position: Mapped[str] = mapped_column(String(80), default="")
    interview_date: Mapped[str] = mapped_column(String(20), default="")
    round_type: Mapped[str] = mapped_column(String(30), default="")  # 技术面/HR面/...
    notes: Mapped[str] = mapped_column(Text, default="")
    review: Mapped[dict] = mapped_column(JSON, default=dict)  # {overall_score, dimensions, summary, suggestions}
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class RealInterviewItem(Base):
    """真实面试中的单条问答。"""

    __tablename__ = "real_interview_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(
        ForeignKey("real_interviews.id", ondelete="CASCADE"), index=True
    )
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text, default="")
    score: Mapped[float] = mapped_column(default=0.0)
    comment: Mapped[str] = mapped_column(Text, default="")

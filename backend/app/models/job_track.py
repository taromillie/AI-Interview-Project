"""岗位收藏与投递跟踪（P2，FR-C-01 增强）。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class JobFavorite(Base):
    """岗位收藏（user_id + position_id 唯一）。"""

    __tablename__ = "job_favorites"
    __table_args__ = (UniqueConstraint("user_id", "position_id", name="uq_fav_user_position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class JobApplication(Base):
    """投递跟踪：用户对某岗位的求职阶段流转。

    status: saved(稍后投) / applied(已投递) / interviewing(面试中) / offer(已获offer) / rejected(未通过)
    """

    __tablename__ = "job_applications"
    __table_args__ = (UniqueConstraint("user_id", "position_id", name="uq_app_user_position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="applied")
    note: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

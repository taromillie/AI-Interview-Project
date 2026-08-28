"""岗位与知识原子（题库）。"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), index=True)          # 如: 后端开发工程师
    direction: Mapped[str] = mapped_column(String(30), default="tech")  # 方向: tech/product/ops...
    difficulty: Mapped[str] = mapped_column(String(10), default="mid")  # junior/mid/senior
    skills: Mapped[list] = mapped_column(JSON, default=list)           # 技能标签列表
    is_public: Mapped[bool] = mapped_column(default=True)
    creator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")   # active / archived
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # ── v1.2：真实招聘数据字段（爬虫/同步填充）──
    company: Mapped[str] = mapped_column(String(120), default="")        # 公司名称
    city: Mapped[str] = mapped_column(String(50), default="")            # 工作地点
    salary_min: Mapped[int | None] = mapped_column(nullable=True)        # 月薪下限（K）
    salary_max: Mapped[int | None] = mapped_column(nullable=True)        # 月薪上限（K）
    description: Mapped[str] = mapped_column(Text, default="")           # 职位描述/工作内容
    welfare: Mapped[list] = mapped_column(JSON, default=list)            # 福利标签（五险一金/双休...）
    source: Mapped[str] = mapped_column(String(20), default="builtin")   # builtin / zhaopin / liepin ...
    source_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)  # 平台职位ID（去重）
    source_url: Mapped[str | None] = mapped_column(String(300), nullable=True)              # 原文链接
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)          # 平台发布时间
    synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)             # 最近同步时间

    knowledge_atoms: Mapped[list["KnowledgeAtom"]] = relationship(back_populates="position")


class KnowledgeAtom(Base):
    """知识原子：题库最小单元，状态机 draft -> published -> archived。"""

    __tablename__ = "knowledge_atoms"

    id: Mapped[int] = mapped_column(primary_key=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"), index=True)
    question: Mapped[str] = mapped_column(Text)                        # 题目
    reference_points: Mapped[list] = mapped_column(JSON, default=list)  # 参考要点
    tags: Mapped[list] = mapped_column(JSON, default=list)             # 技能标签
    difficulty: Mapped[str] = mapped_column(String(10), default="mid")
    status: Mapped[str] = mapped_column(String(20), default="draft")    # draft/published/archived
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    position: Mapped["Position"] = relationship(back_populates="knowledge_atoms")

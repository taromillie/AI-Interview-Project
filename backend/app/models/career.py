"""能力画像、转行规划与谈薪评估。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AbilityProfile(Base):
    """多场面试聚合出的能力画像（雷达图数据源）。"""

    __tablename__ = "ability_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    dimensions: Mapped[dict] = mapped_column(JSON, default=dict)  # {tech, expression, logic, project}
    skill_scores: Mapped[dict] = mapped_column(JSON, default=dict)  # {skill: score}
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class CareerPlan(Base):
    """转行诊断结果：可迁移技能 + 缺口 + 发展路径。"""

    __tablename__ = "career_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    from_position: Mapped[str] = mapped_column(String(80))
    to_position: Mapped[str] = mapped_column(String(80))
    transferable: Mapped[list] = mapped_column(JSON, default=list)   # [{skill, evidence}]
    gaps: Mapped[list] = mapped_column(JSON, default=list)          # [{skill, level}]
    roadmap: Mapped[list] = mapped_column(JSON, default=list)       # 学习路径
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SalaryEval(Base):
    """谈薪评估结果。"""

    __tablename__ = "salary_evals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    skill_stack: Mapped[list] = mapped_column(JSON, default=list)
    years: Mapped[int] = mapped_column(default=0)
    city: Mapped[str] = mapped_column(String(50))
    target_position: Mapped[str] = mapped_column(String(80))
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    # {salary_range: [min,mid,max], factors: [], strategy: []}
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

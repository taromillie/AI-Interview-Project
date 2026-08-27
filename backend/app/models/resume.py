"""简历画像与简历×JD 匹配诊断。"""
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200), default="")  # 用户自定义名称（空则前端用自动名）
    file_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_json: Mapped[dict] = mapped_column(JSON, default=dict)  # 结构化画像
    skills: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class JobDescription(Base):
    """用户保存的岗位 JD 历史。"""
    __tablename__ = "job_descriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class MatchDiagnostic(Base):
    __tablename__ = "match_diagnostics"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id"), nullable=True)
    jd_text: Mapped[str] = mapped_column(Text)
    match_score: Mapped[float] = mapped_column(Float, default=0.0)   # 0-100
    gaps: Mapped[list] = mapped_column(JSON, default=list)          # [{skill, required_level, current_level, suggestion}]
    suggestions: Mapped[list] = mapped_column(JSON, default=list)   # 简历优化建议
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

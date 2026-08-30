"""面试会话、消息流与复盘报告。"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    position_id: Mapped[int | None] = mapped_column(ForeignKey("positions.id"), nullable=True)
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id"), nullable=True)
    interviewer_id: Mapped[int | None] = mapped_column(ForeignKey("interviewers.id"), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(10), default="normal")  # easy/normal/hard
    mode: Mapped[str] = mapped_column(String(10), default="text")    # text / voice / video
    interview_type: Mapped[str] = mapped_column(String(20), default="normal")  # normal/switch/salary
    status: Mapped[str] = mapped_column(String(20), default="created")
    # created/warming/asking/decide_next/finishing/reported
    config: Mapped[dict] = mapped_column(JSON, default=dict)          # 面试配置（轮数、人设等）
    max_rounds: Mapped[int] = mapped_column(Integer, default=6)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class InterviewMessage(Base):
    __tablename__ = "interview_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"), index=True)
    role: Mapped[str] = mapped_column(String(10))                    # user / assistant
    content: Mapped[str] = mapped_column(Text)
    strategy: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # deep_dive/remedy/switch_topic/project_probe/none
    evidence_atom_ids: Mapped[list] = mapped_column(JSON, default=list)  # 关联知识原子
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"), unique=True, index=True)
    overall_score: Mapped[float] = mapped_column(default=0.0)
    dimensions: Mapped[dict] = mapped_column(JSON, default=dict)      # {tech, expression, logic, project}
    question_feedback: Mapped[list] = mapped_column(JSON, default=list)
    weak_points: Mapped[list] = mapped_column(JSON, default=list)     # 弱点标签
    summary: Mapped[str] = mapped_column(Text, default="")            # 总评与建议
    coverage: Mapped[dict] = mapped_column(JSON, default=dict)        # {covered:[], uncovered:[]}
    learning_path: Mapped[list] = mapped_column(JSON, default=list)   # [{phase,duration,action}]
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

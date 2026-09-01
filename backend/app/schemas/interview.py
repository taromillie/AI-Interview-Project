"""面试与复盘契约。"""
from pydantic import BaseModel, Field, field_validator


class InterviewCreateRequest(BaseModel):
    position_id: int | None = None          # 题库岗位（选择题库时使用）
    target_position: str | None = None      # 目标岗位文本（JD 选项或自定义输入时使用）
    resume_id: int | None = None
    interviewer_id: int | None = None       # 面试官角色（v1.1，默认用通用技术面）
    difficulty: str = Field(default="normal", pattern="^(easy|normal|hard)$")  # 面试难度档位
    mode: str = Field(default="text", pattern="^(text|voice|video)$")
    interview_type: str = Field(default="normal", pattern="^(normal|switch|salary)$")
    max_rounds: int = Field(default=6, ge=1, le=20)
    config: dict = Field(default_factory=dict)


class InterviewOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    position_id: int | None = None
    position_name: str | None = None
    target_position: str | None = None
    resume_id: int | None = None
    interviewer_id: int | None = None
    interviewer_name: str | None = None
    difficulty: str | None = None
    mode: str
    interview_type: str
    status: str
    max_rounds: int
    created_at: object | None = None
    report_id: int | None = None
    overall_score: float | None = None
    message_count: int | None = None
    report_generating: bool = False  # 占位报告（复盘生成中）标记，前端据此展示“分析中”


class InterviewMessageOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    role: str
    content: str
    strategy: str | None = None
    created_at: object | None = None


class ReportOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    interview_id: int
    overall_score: float
    dimensions: dict
    question_feedback: list
    weak_points: list
    summary: str = ""
    coverage: dict = {}
    learning_path: list = []
    # pending=后台生成中 / ready=AI 完整报告 / fallback=AI 降级规则报告 / failed=生成失败可重试
    status: str = "pending"

    # 旧数据迁移后这些列可能为 NULL：统一兜底为默认值，避免 500
    @field_validator("status", mode="before")
    @classmethod
    def _status_or_default(cls, v):
        return v if v is not None else "pending"
    @field_validator("dimensions", "coverage", mode="before")
    @classmethod
    def _dict_or_default(cls, v):
        return v if v is not None else {}

    @field_validator("question_feedback", "weak_points", "learning_path", mode="before")
    @classmethod
    def _list_or_default(cls, v):
        return v if v is not None else []

    @field_validator("summary", mode="before")
    @classmethod
    def _summary_or_default(cls, v):
        return v if v is not None else ""

    @field_validator("overall_score", mode="before")
    @classmethod
    def _score_or_default(cls, v):
        return v if v is not None else 0.0


class InterviewDetailOut(InterviewOut):
    messages: list[InterviewMessageOut] = Field(default_factory=list)
    report: ReportOut | None = None


class AnswerRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    # 断线重发幂等键：同一 request_id 的重复提交直接重放结果，避免回答被重复记录
    request_id: str | None = Field(default=None, max_length=64)

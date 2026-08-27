"""面试与复盘契约。"""
from pydantic import BaseModel, Field


class InterviewCreateRequest(BaseModel):
    position_id: int | None = None
    resume_id: int | None = None
    mode: str = Field(default="text", pattern="^(text|voice|video)$")
    interview_type: str = Field(default="normal", pattern="^(normal|switch|salary)$")
    max_rounds: int = Field(default=6, ge=1, le=20)
    config: dict = Field(default_factory=dict)


class InterviewOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    mode: str
    interview_type: str
    status: str
    max_rounds: int


class AnswerRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class ReportOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    interview_id: int
    overall_score: float
    dimensions: dict
    question_feedback: list
    weak_points: list

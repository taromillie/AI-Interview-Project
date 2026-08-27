"""真实面试复盘契约。"""
from pydantic import BaseModel, Field


class RealInterviewItemIn(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    answer: str = Field(default="", max_length=4000)


class RealInterviewCreate(BaseModel):
    company: str = Field(min_length=1, max_length=80)
    position: str = Field(default="", max_length=80)
    interview_date: str = Field(default="", max_length=20)
    round_type: str = Field(default="", max_length=30)
    notes: str = Field(default="", max_length=2000)
    items: list[RealInterviewItemIn] = Field(default_factory=list)


class RealInterviewOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    company: str
    position: str
    interview_date: str
    round_type: str
    notes: str
    review: dict = Field(default_factory=dict)
    items: list[dict] = Field(default_factory=list)
    created_at: object | None = None


class RealInterviewSummaryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    company: str
    position: str
    interview_date: str
    round_type: str
    review: dict = Field(default_factory=dict)
    created_at: object | None = None

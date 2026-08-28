"""面试官角色契约。"""
from pydantic import BaseModel, Field


class InterviewerCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    title: str = Field(default="", max_length=80)
    persona: str = Field(default="")
    style: str = Field(default="")
    interview_type: str = Field(default="all", pattern="^(all|normal|switch|salary)$")
    difficulty_bias: int = Field(default=0, ge=-1, le=1)


class InterviewerOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    title: str
    persona: str
    style: str
    interview_type: str
    difficulty_bias: int
    is_public: bool
    created_by: int | None = None

"""简历×JD 诊断契约（与需求文档数据规格一致）。"""
from pydantic import BaseModel, Field


class GapItem(BaseModel):
    skill: str
    required_level: str
    current_level: str
    suggestion: str


class ResumeDiagnosticRequest(BaseModel):
    jd_text: str = Field(min_length=20, max_length=20_000)


class ResumeDiagnosticOut(BaseModel):
    match_score: float = Field(ge=0, le=100)
    gaps: list[GapItem]
    resume_suggestions: list[str]


class ResumeOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    skills: list[str]
    created_at: object | None = None

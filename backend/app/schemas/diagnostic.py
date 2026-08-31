"""简历×JD 诊断契约（与需求文档数据规格一致）。"""
from pydantic import BaseModel, Field


class GapItem(BaseModel):
    skill: str
    required_level: str
    current_level: str
    suggestion: str


class ResumeDiagnosticRequest(BaseModel):
    jd_text: str | None = Field(default=None, max_length=20_000)
    resume_id: int | None = Field(default=None, description="指定用于诊断的简历，缺省用最近一份")
    jd_id: int | None = Field(default=None, description="指定历史 JD，缺省用 jd_text")


class ResumeDiagnosticOut(BaseModel):
    diagnostic_id: int
    match_score: float = Field(ge=0, le=100)
    gaps: list[GapItem]
    resume_suggestions: list[str]


class MatchDiagnosticOut(BaseModel):
    """历史诊断记录（列表即详情，前端可直接渲染报告）。"""
    id: int
    resume_id: int | None = None
    resume_name: str = ""
    jd_excerpt: str = ""
    match_score: float = Field(ge=0, le=100)
    gaps: list[GapItem]
    suggestions: list[str]
    created_at: object | None = None


class ResumeOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str = ""
    skills: list[str]
    raw_text: str | None = None
    created_at: object | None = None


class JDRequest(BaseModel):
    title: str = Field(default="", max_length=200)
    content: str = Field(min_length=20, max_length=20_000)


class JDOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    content: str
    created_at: object | None = None

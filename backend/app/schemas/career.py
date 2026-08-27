"""转行诊断与谈薪评估契约。"""
from pydantic import BaseModel, Field


class CareerDiagnosisRequest(BaseModel):
    from_position: str = Field(min_length=1, max_length=80)
    to_position: str = Field(min_length=1, max_length=80)
    resume_id: int | None = None


class CareerDiagnosisOut(BaseModel):
    transferable: list[dict] = Field(default_factory=list)   # [{skill, evidence}]
    gaps: list[dict] = Field(default_factory=list)          # [{skill, level}]
    roadmap: list[dict] = Field(default_factory=list)       # 学习路径
    summary: str = ""


class SalaryEvalRequest(BaseModel):
    skill_stack: list[str] = Field(default_factory=list)
    years: int = Field(ge=0, le=60)
    city: str = Field(min_length=1, max_length=50)
    target_position: str = Field(min_length=1, max_length=80)


class SalaryEvalOut(BaseModel):
    salary_range: list[int] = Field(default_factory=list)   # [min, mid, max]
    factors: list[str] = Field(default_factory=list)
    strategy: list[str] = Field(default_factory=list)

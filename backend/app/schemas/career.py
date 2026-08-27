"""转行诊断与谈薪评估契约。"""
from pydantic import BaseModel, Field


class CareerDiagnosisRequest(BaseModel):
    from_position: str = Field(min_length=1, max_length=80)
    to_position: str = Field(min_length=1, max_length=80)
    resume_id: int | None = None


class CareerDiagnosisOut(BaseModel):
    id: int | None = None
    transferable: list[dict] = Field(default_factory=list)   # [{skill, evidence}]
    gaps: list[dict] = Field(default_factory=list)          # [{skill, level}]
    roadmap: list[dict] = Field(default_factory=list)       # 学习路径
    transition_projects: list[dict] = Field(default_factory=list)  # [{name, description, duration}]
    summary: str = ""


class CareerPlanOut(BaseModel):
    """转行诊断历史记录。"""

    model_config = {"from_attributes": True}

    id: int
    from_position: str
    to_position: str
    transferable: list[dict] = Field(default_factory=list)
    gaps: list[dict] = Field(default_factory=list)
    roadmap: list[dict] = Field(default_factory=list)
    transition_projects: list[dict] = Field(default_factory=list)
    summary: str = ""
    created_at: object | None = None


class SalaryEvalRequest(BaseModel):
    skill_stack: list[str] = Field(default_factory=list)
    years: int = Field(ge=0, le=60)
    city: str = Field(min_length=1, max_length=50)
    target_position: str = Field(min_length=1, max_length=80)
    resume_id: int | None = Field(
        default=None,
        description="指定结合的简历；None=最近一份，-1=不结合，>0=指定简历",
    )


class SalaryEvalOut(BaseModel):
    id: int | None = None
    salary_range: list[int] = Field(default_factory=list)   # [min, mid, max]
    factors: list[str] = Field(default_factory=list)
    strategy: list[str] = Field(default_factory=list)


class SalaryEvalHistoryOut(BaseModel):
    """谈薪评估历史记录。"""

    model_config = {"from_attributes": True}

    id: int
    skill_stack: list[str] = Field(default_factory=list)
    years: int = 0
    city: str = ""
    target_position: str = ""
    result: dict = Field(default_factory=dict)              # {salary_range, factors, strategy}
    created_at: object | None = None


class ProfileOut(BaseModel):
    """能力画像（多场面试聚合）。"""

    dimensions: dict = Field(default_factory=dict)          # {tech, expression, logic, project}
    skill_scores: dict = Field(default_factory=dict)        # {skill: score}
    weak_points: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)      # 优势项（模板生成）
    suggestions: list[str] = Field(default_factory=list)    # 提升建议（模板生成）
    trend: list[dict] = Field(default_factory=list)         # 维度趋势 [{report_id, created_at, dimensions}]
    report_count: int = 0
    updated_at: object | None = None

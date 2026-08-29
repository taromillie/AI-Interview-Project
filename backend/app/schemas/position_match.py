"""简历→岗位智能匹配契约。"""
from datetime import datetime

from pydantic import BaseModel, Field


class DimensionBreakdown(BaseModel):
    skill_score: float
    direction_score: float
    exp_score: float


class PositionMatchItem(BaseModel):
    position_id: int
    name: str
    direction: str
    difficulty: str
    skills: list[str]
    company: str = ""
    city: str = ""
    salary_min: int | None = None
    salary_max: int | None = None
    description: str = ""
    match_score: float = Field(ge=0, le=100)
    matched_skills: list[str]
    missing_skills: list[str]
    reason: str = ""
    dimension_breakdown: DimensionBreakdown


class MatchPositionsRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=50)
    direction: str | None = None
    city: str | None = None
    difficulty: str | None = None


class PositionMatchOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    position_id: int
    position_name: str = ""
    company: str = ""
    city: str = ""
    salary_min: int | None = None
    salary_max: int | None = None
    direction: str = ""
    difficulty: str = ""
    skills: list[str] = []
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    reason: str = ""
    created_at: object | None = None


class MatchPositionsOut(BaseModel):
    resume_id: int
    resume_name: str = ""
    matched_at: object | None = None
    results: list[PositionMatchItem]

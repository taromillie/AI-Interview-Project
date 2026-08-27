"""备战日历契约。"""
from pydantic import BaseModel, Field


class StudyPlanGenerateRequest(BaseModel):
    target_position: str = Field(default="", max_length=80, description="目标岗位（可空，空则结合能力画像）")
    days: int = Field(default=14, ge=3, le=60, description="备战天数")
    resume_id: int | None = None


class StudyPlanTaskIn(BaseModel):
    day: int
    done: bool = False


class StudyPlanOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    target_position: str
    days: int
    tasks: list[dict] = Field(default_factory=list)
    status: str = "active"
    summary: str = ""
    created_at: object | None = None

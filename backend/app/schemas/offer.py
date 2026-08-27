"""Offer 对比契约。"""
from pydantic import BaseModel, Field


class OfferCreate(BaseModel):
    company: str = Field(min_length=1, max_length=80)
    position: str = Field(default="", max_length=80)
    city: str = Field(default="", max_length=50)
    monthly_salary: int = Field(default=0, ge=0)
    bonus_months: int = Field(default=0, ge=0, le=24)
    stock_value: int = Field(default=0, ge=0)
    work_balance: int = Field(default=0, ge=0, le=10)
    benefits: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=1000)


class OfferOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    company: str
    position: str
    city: str
    monthly_salary: int
    bonus_months: int
    stock_value: int
    work_balance: int
    benefits: str
    notes: str
    created_at: object | None = None


class OfferCompareOut(BaseModel):
    """多个 offer 的结构化对比 + AI 建议。"""

    table: list[dict] = Field(default_factory=list)   # [{field, values: [..]}]
    analysis: str = ""                                 # AI 综合建议

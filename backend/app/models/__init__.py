"""ORM 模型统一导出，确保 init_db 时全部注册。"""
from app.models.career import AbilityProfile, CareerPlan, SalaryEval
from app.models.interview import Interview, InterviewMessage, Report
from app.models.position import KnowledgeAtom, Position
from app.models.resume import JobDescription, MatchDiagnostic, Resume
from app.models.user import LlmProvider, User

__all__ = [
    "User",
    "LlmProvider",
    "Position",
    "KnowledgeAtom",
    "Resume",
    "JobDescription",
    "MatchDiagnostic",
    "Interview",
    "InterviewMessage",
    "Report",
    "AbilityProfile",
    "CareerPlan",
    "SalaryEval",
]

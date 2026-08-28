"""ORM 模型统一导出，确保 init_db 时全部注册。"""
from app.models.career import AbilityProfile, CareerPlan, SalaryEval
from app.models.interview import Interview, InterviewMessage, Report
from app.models.interviewer import Interviewer
from app.models.offer import Offer
from app.models.position import KnowledgeAtom, Position
from app.models.real_interview import RealInterview, RealInterviewItem
from app.models.resume import JobDescription, MatchDiagnostic, Resume
from app.models.study import StudyPlan
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
    "Interviewer",
    "AbilityProfile",
    "CareerPlan",
    "SalaryEval",
    "StudyPlan",
    "RealInterview",
    "RealInterviewItem",
    "Offer",
]

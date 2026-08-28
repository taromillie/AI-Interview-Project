"""面试与报告的只读查询，集中处理归属校验之外的查询组合。"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.interview import Interview, InterviewMessage, Report


class InterviewRepository:
    """面试历史、消息和报告查询。"""

    def list_by_user(self, db: Session, user_id: int, limit: int = 50) -> list[Interview]:
        return list(
            db.scalars(
                select(Interview)
                .where(Interview.user_id == user_id)
                .order_by(Interview.id.desc())
                .limit(limit)
            ).all()
        )

    def messages(self, db: Session, interview_id: int) -> list[InterviewMessage]:
        return list(
            db.scalars(
                select(InterviewMessage)
                .where(InterviewMessage.interview_id == interview_id)
                .order_by(InterviewMessage.id)
            ).all()
        )

    def report(self, db: Session, interview_id: int) -> Report | None:
        return db.scalar(select(Report).where(Report.interview_id == interview_id))

    def message_count(self, db: Session, interview_id: int) -> int:
        return int(
            db.scalar(
                select(func.count())
                .select_from(InterviewMessage)
                .where(InterviewMessage.interview_id == interview_id)
            )
            or 0
        )


class UserDataRepository:
    """按用户过滤的通用历史记录查询。"""

    def list_career_plans(self, db: Session, user_id: int, limit: int = 20):
        from app.models.career import CareerPlan

        return list(
            db.scalars(
                select(CareerPlan)
                .where(CareerPlan.user_id == user_id)
                .order_by(CareerPlan.id.desc())
                .limit(limit)
            ).all()
        )

    def list_salary_evals(self, db: Session, user_id: int, limit: int = 20):
        from app.models.career import SalaryEval

        return list(
            db.scalars(
                select(SalaryEval)
                .where(SalaryEval.user_id == user_id)
                .order_by(SalaryEval.id.desc())
                .limit(limit)
            ).all()
        )

    def list_study_plans(self, db: Session, user_id: int, limit: int = 20):
        from app.models.study import StudyPlan

        return list(
            db.scalars(
                select(StudyPlan)
                .where(StudyPlan.user_id == user_id)
                .order_by(StudyPlan.id.desc())
                .limit(limit)
            ).all()
        )

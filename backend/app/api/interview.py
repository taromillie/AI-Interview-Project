"""模拟面试接口（含 SSE 对话流）。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.interview import AnswerRequest, InterviewCreateRequest, InterviewOut

router = APIRouter(prefix="/interviews", tags=["模拟面试"])


@router.post("", response_model=InterviewOut, status_code=201)
def create_interview(
    payload: InterviewCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # TODO(Phase 2): 创建面试会话并初始化状态机
    raise NotImplementedError("面试编排器将在下一阶段实现")


@router.post("/{interview_id}/answer")
def submit_answer(
    interview_id: int,
    payload: AnswerRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # TODO(Phase 2): 提交回答，驱动动态 RAG 决策
    raise NotImplementedError("面试编排器将在下一阶段实现")


@router.post("/{interview_id}/finish")
def finish_interview(
    interview_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # TODO(Phase 2): 结束面试并触发报告生成
    raise NotImplementedError("面试编排器将在下一阶段实现")

"""面试官角色接口（角色库查询 / 用户自建）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.interviewer import Interviewer
from app.models.user import User
from app.schemas.interviewer import InterviewerCreateRequest, InterviewerOut

router = APIRouter(prefix="/interviewers", tags=["面试官角色"])

# 内置面试官角色库（is_public=True，ADMIN 可维护；首次访问时自动初始化）
BUILTIN_INTERVIEWERS = [
    {
        "name": "资深技术面试官",
        "title": "标准技术面 · 通用",
        "persona": "你是一位有 8 年一线研发经验、多次担任校招社招面试官的资深工程师。语气平和但专业，关注候选人是否真的动手做过事情。",
        "style": "先肯定再追问；喜欢让候选人用具体例子证明自己；对技术细节较真但不苛刻。",
        "interview_type": "normal",
        "difficulty_bias": 0,
    },
    {
        "name": "CTO 技术面",
        "title": "架构视角 · 深挖原理",
        "persona": "你是一家公司的 CTO，负责把关技术团队的每一份 Offer。你非常重视候选人解决问题的深度、系统设计能力与对底层原理的理解。",
        "style": "喜欢从场景出发层层深挖：先给业务场景，再追问「为什么这么设计」「换个场景会怎样」；对模糊回答会继续追问直到给出确定性结论。",
        "interview_type": "all",
        "difficulty_bias": 1,
    },
    {
        "name": "HR 综合面",
        "title": "综合素质 · 软实力",
        "persona": "你是一位经验丰富的 HR，负责评估候选人的综合素质：表达逻辑、沟通协作、稳定性、职业规划与匹配度。",
        "style": "节奏轻松自然，但每个问题都暗含考察点；关注候选人自我认知是否清晰、回答是否结构化。",
        "interview_type": "all",
        "difficulty_bias": -1,
    },
    {
        "name": "压力面",
        "title": "高压场景 · 抗压测试",
        "persona": "你是一位以严格著称的面试官，刻意营造高压环境，测试候选人面对质疑时的情绪控制与应变能力。",
        "style": "会直接质疑候选人的回答、提出反例、连续追漏洞；措辞直接不留情面，但始终就事论事不进行人身攻击。",
        "interview_type": "all",
        "difficulty_bias": 1,
    },
    {
        "name": "转行质疑面试官",
        "title": "转行专属 · 挑战认知",
        "persona": "你是一位对转行候选人持有审慎态度的面试官，常见于跨行业/跨岗位的求职场景。你了解候选人的原行业背景，也清楚转行者的常见短板。",
        "style": "会先给候选人机会证明可迁移能力，再针对「为什么转行」「原行业经验如何复用」「是否只是一时冲动」等核心质疑点连续提问。",
        "interview_type": "switch",
        "difficulty_bias": 0,
    },
    {
        "name": "谈薪 HR",
        "title": "谈薪模式 · 谈判演练",
        "persona": "你是一位擅长薪酬谈判的 HR，正在进行谈薪环节的模拟演练。你会模拟真实谈判中 HR 的施压话术（压期望、谈市场行情、抛福利组合）。",
        "style": "围绕期望薪资、薪资构成、跳槽涨幅、福利预期展开谈判，帮助候选人练习有策略地争取最优 package。",
        "interview_type": "salary",
        "difficulty_bias": 0,
    },
]


def _seed_builtin(db: Session) -> None:
    """公共角色库为空时自动初始化内置角色（幂等）。"""
    exists = db.scalar(select(Interviewer.id).where(Interviewer.is_public == True).limit(1))  # noqa: E712
    if exists is not None:
        return
    for item in BUILTIN_INTERVIEWERS:
        db.add(Interviewer(is_public=True, created_by=None, **item))
    db.commit()


@router.get("", response_model=list[InterviewerOut])
def list_interviewers(
    interview_type: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """面试官角色列表：内置公开角色 + 本人自建角色。"""
    _seed_builtin(db)
    stmt = select(Interviewer).where(or_(Interviewer.is_public == True, Interviewer.created_by == user.id))  # noqa: E712
    if interview_type and interview_type != "all":
        stmt = stmt.where(
            or_(Interviewer.interview_type == "all", Interviewer.interview_type == interview_type)
        )
    return db.scalars(stmt.order_by(Interviewer.id)).all()


@router.post("", response_model=InterviewerOut, status_code=201)
def create_interviewer(
    payload: InterviewerCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """用户自建面试官角色。"""
    interviewer = Interviewer(
        is_public=False,
        created_by=user.id,
        **payload.model_dump(),
    )
    db.add(interviewer)
    db.commit()
    db.refresh(interviewer)
    return interviewer


@router.delete("/{interviewer_id}", status_code=204)
def delete_interviewer(
    interviewer_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除本人自建角色（内置角色不可删）。"""
    interviewer = db.get(Interviewer, interviewer_id)
    if interviewer is None or interviewer.created_by != user.id:
        raise HTTPException(404, "面试官角色不存在")
    db.delete(interviewer)
    db.commit()

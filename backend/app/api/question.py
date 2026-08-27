"""题库管理接口（知识原子 CRUD，ADMIN 发布）。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.db import get_db
from app.models.position import KnowledgeAtom, Position
from app.models.user import User

router = APIRouter(prefix="/questions", tags=["题库管理"])


@router.get("")
def list_atoms(
    position_id: int | None = None,
    status: str | None = Query(default=None, pattern="^(draft|published|archived)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """题库列表：管理员可见全部；普通用户仅可见已发布公共题 + 本人草稿。"""
    stmt = select(KnowledgeAtom)
    if position_id:
        stmt = stmt.where(KnowledgeAtom.position_id == position_id)
    if user.role == "admin":
        if status:
            stmt = stmt.where(KnowledgeAtom.status == status)
        return db.scalars(stmt).all()
    if status == "draft":
        stmt = stmt.where(
            KnowledgeAtom.status == "draft",
            KnowledgeAtom.created_by == user.id,
        )
    elif status == "archived":
        stmt = stmt.where(
            KnowledgeAtom.status == "archived",
            KnowledgeAtom.created_by == user.id,
        )
    else:
        stmt = stmt.where(
            or_(
                KnowledgeAtom.status == "published",
                and_(KnowledgeAtom.status == "draft", KnowledgeAtom.created_by == user.id),
            )
        )
    return db.scalars(stmt).all()


@router.get("/positions")
def list_positions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Position).where(Position.status == "active")).all()


@router.post("", status_code=201)
def create_atom(
    position_id: int,
    question: str,
    reference_points: list[str] | None = None,
    tags: list[str] | None = None,
    difficulty: str = "mid",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    position = db.get(Position, position_id)
    if position is None:
        raise HTTPException(status_code=404, detail="岗位不存在")
    atom = KnowledgeAtom(
        position_id=position_id,
        question=question,
        reference_points=reference_points or [],
        tags=tags or [],
        difficulty=difficulty,
        status="draft",
        created_by=user.id,
    )
    db.add(atom)
    db.commit()
    db.refresh(atom)
    return atom


@router.post("/{atom_id}/publish")
def publish_atom(
    atom_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """仅管理员可发布知识原子（约束：仅 published 进入面试追问链路）。"""
    atom = db.get(KnowledgeAtom, atom_id)
    if atom is None:
        raise HTTPException(status_code=404, detail="知识原子不存在")
    atom.status = "published"
    db.commit()
    db.refresh(atom)
    return atom

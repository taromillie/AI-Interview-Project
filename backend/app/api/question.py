"""题库管理接口（知识原子 CRUD，ADMIN 发布）。"""
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import String, and_, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.db import get_db
from app.models.position import KnowledgeAtom, Position
from app.models.user import User

router = APIRouter(prefix="/questions", tags=["题库管理"])

# 内置岗位库（is_public=True，ADMIN 可维护；首次访问时自动初始化）
BUILTIN_POSITIONS = [
    {
        "name": "后端开发工程师",
        "direction": "backend",
        "difficulty": "mid",
        "skills": ["Python", "Java", "MySQL", "Redis", "消息队列", "分布式"],
    },
    {
        "name": "Java 开发工程师",
        "direction": "backend",
        "difficulty": "mid",
        "skills": ["Java", "Spring Boot", "MyBatis", "MySQL", "JVM", "微服务"],
    },
    {
        "name": "全栈开发工程师",
        "direction": "backend",
        "difficulty": "senior",
        "skills": ["Vue", "React", "Node.js", "Go", "系统设计", "Docker"],
    },
    {
        "name": "测试开发工程师",
        "direction": "backend",
        "difficulty": "junior",
        "skills": ["pytest", "接口测试", "自动化测试", "Selenium", "Linux"],
    },
    {
        "name": "前端开发工程师",
        "direction": "frontend",
        "difficulty": "mid",
        "skills": ["HTML/CSS", "JavaScript", "TypeScript", "Vue", "工程化", "性能优化"],
    },
    {
        "name": "前端架构工程师",
        "direction": "frontend",
        "difficulty": "senior",
        "skills": ["React", "架构设计", "微前端", "Node.js", "性能优化", "工程化"],
    },
    {
        "name": "算法工程师",
        "direction": "algorithm",
        "difficulty": "senior",
        "skills": ["机器学习", "深度学习", "Python", "PyTorch", "数据结构", "数学基础"],
    },
    {
        "name": "推荐算法工程师",
        "direction": "algorithm",
        "difficulty": "senior",
        "skills": ["推荐系统", "召回排序", "特征工程", "A/B 测试", "Python"],
    },
    {
        "name": "产品经理",
        "direction": "product",
        "difficulty": "mid",
        "skills": ["需求分析", "PRD", "数据分析", "项目管理", "用户研究"],
    },
    {
        "name": "AI 产品经理",
        "direction": "product",
        "difficulty": "senior",
        "skills": ["大模型应用", "需求分析", "数据分析", "Prompt 设计", "商业化"],
    },
    {
        "name": "数据分析师",
        "direction": "data",
        "difficulty": "junior",
        "skills": ["SQL", "Python", "Excel", "数据可视化", "A/B 测试"],
    },
    {
        "name": "数据仓库工程师",
        "direction": "data",
        "difficulty": "senior",
        "skills": ["数仓建模", "ETL", "Hive", "Spark", "Flink", "Doris"],
    },
    {
        "name": "运营专员",
        "direction": "operations",
        "difficulty": "junior",
        "skills": ["内容运营", "活动策划", "用户增长", "数据分析", "文案"],
    },
    {
        "name": "用户增长运营",
        "direction": "operations",
        "difficulty": "mid",
        "skills": ["增长黑客", "渠道投放", "用户运营", "数据分析", "私域运营"],
    },
]


def _seed_builtin_positions(db: Session) -> None:
    """公共岗位库为空且显式启用 builtin 数据源时，才自动初始化内置岗位（幂等）。

    默认数据源为 jobui（职友集真实数据），不再注入示例岗位。
    """
    from app.core.config import settings

    if "builtin" not in settings.JOB_SOURCE_ENABLED:
        return
    exists = db.scalar(select(Position.id).where(Position.status == "active").limit(1))
    if exists is not None:
        return
    for item in BUILTIN_POSITIONS:
        db.add(Position(is_public=True, creator_id=None, **item))
    db.commit()


@router.get("")
def list_atoms(
    position_id: int | None = None,
    status: str | None = Query(default=None, pattern="^(draft|published|archived)$"),
    keyword: str | None = None,
    tag: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """题库列表：管理员可见全部；普通用户仅可见已发布公共题 + 本人草稿。

    tag 参数按标签精确匹配（JSON 数组包含）。
    """
    stmt = select(KnowledgeAtom)
    if position_id:
        stmt = stmt.where(KnowledgeAtom.position_id == position_id)
    if tag:
        tag_value = tag.strip()
        if tag_value:
            stmt = stmt.where(func.cast(KnowledgeAtom.tags, String).like(f'%"{tag_value}"%'))
    if keyword:
        kw = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(
                KnowledgeAtom.question.ilike(kw),
                func.cast(KnowledgeAtom.tags, String).ilike(kw),
            )
        )
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
    """岗位列表：内置岗位库为空时自动初始化。"""
    _seed_builtin_positions(db)
    return db.scalars(select(Position).where(Position.status == "active").order_by(Position.id)).all()


class ImportRequest(BaseModel):
    position_id: int
    format: str = "auto"  # auto / json / markdown
    text: str


@router.post("/import", status_code=201)
def import_atoms_api(
    payload: ImportRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """批量导入题目（JSON / Markdown，自动识别或显式指定）。

    结果：created 新建条数；skipped 同岗位重复跳过；errors 逐行错误明细。
    """
    from app.services.question_import import import_atoms, parse_auto, parse_json, parse_markdown

    try:
        if payload.format == "json":
            items = parse_json(payload.text)
        elif payload.format == "markdown":
            items = parse_markdown(payload.text)
        else:
            items = parse_auto(payload.text)
        result = import_atoms(db, user, payload.position_id, items)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=f"解析失败：{exc}")
    return result


@router.post("/positions/sync")
def trigger_position_sync(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """手动触发一次岗位采集同步（真实数据源）。"""
    from app.services.job_crawler import sync_jobs

    stats = sync_jobs(db=db)
    if stats.get("skipped"):
        return {"ok": False, "reason": stats.get("reason", "已有同步任务进行中"), "stats": stats}
    return {"ok": True, "stats": stats}


@router.get("/positions/sync-config")
def get_sync_config(user: User = Depends(get_current_user)):
    """获取岗位自动同步配置与最近同步时间。"""
    from app.services.sync_state import get_sync_state

    return get_sync_state()


@router.post("/positions/sync-config")
def set_sync_config(
    auto_enabled: bool | None = None,
    interval_minutes: int | None = None,
    user: User = Depends(get_current_user),
):
    """调整岗位自动同步频率（分钟）。interval_minutes 最短 5 分钟。"""
    from app.services.sync_state import update_sync_config

    return update_sync_config(auto_enabled=auto_enabled, interval_minutes=interval_minutes)


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

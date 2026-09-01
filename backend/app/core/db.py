"""数据库引擎与会话管理（SQLAlchemy 2.0）。"""
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# timeout=30 等价于 SQLite busy_timeout=30000ms：后台任务写库时，并发读请求等待而非立刻报"database is locked"
connect_args = (
    {"check_same_thread": False, "timeout": 30}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：请求级数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_column(conn, table: str, column: str, ddl: str) -> None:
    """SQLite 轻量迁移：表已存在时补充缺失列（create_all 不会给已有表加列）。"""
    rows = conn.execute(text(f'PRAGMA table_info("{table}")')).fetchall()
    cols = {r[1] for r in rows}
    if column not in cols:
        conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN {ddl}'))


def init_db() -> None:
    """开发阶段直接建表；生产环境建议使用 Alembic 迁移。"""
    from app import models  # noqa: F401  确保模型已注册

    Base.metadata.create_all(bind=engine)

    if settings.DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            # WAL 模式：读写不互斥，避免后台报告生成与请求并发时互相阻塞（导致 500）
            conn.execute(text("PRAGMA journal_mode=WAL"))
            _ensure_column(conn, "career_plans", "summary", "summary TEXT DEFAULT ''")
            _ensure_column(conn, "career_plans", "transition_projects", "transition_projects JSON")
            _ensure_column(conn, "resumes", "name", "name VARCHAR(200) NOT NULL DEFAULT ''")
            # v1.1：面试增加面试官角色与难度
            _ensure_column(conn, "interviews", "interviewer_id", "interviewer_id INTEGER")
            _ensure_column(conn, "interviews", "difficulty", "difficulty VARCHAR(10) NOT NULL DEFAULT 'normal'")
            # v1.2：岗位增加真实招聘数据字段
            _ensure_column(conn, "positions", "company", "company VARCHAR(120) NOT NULL DEFAULT ''")
            _ensure_column(conn, "positions", "city", "city VARCHAR(50) NOT NULL DEFAULT ''")
            _ensure_column(conn, "positions", "salary_min", "salary_min INTEGER")
            _ensure_column(conn, "positions", "salary_max", "salary_max INTEGER")
            _ensure_column(conn, "positions", "description", "description TEXT NOT NULL DEFAULT ''")
            _ensure_column(conn, "positions", "welfare", "welfare JSON")
            _ensure_column(conn, "positions", "source", "source VARCHAR(20) NOT NULL DEFAULT 'builtin'")
            _ensure_column(conn, "positions", "source_id", "source_id VARCHAR(100)")
            _ensure_column(conn, "positions", "source_url", "source_url VARCHAR(300)")
            _ensure_column(conn, "positions", "published_at", "published_at DATETIME")
            _ensure_column(conn, "positions", "synced_at", "synced_at DATETIME")
            # v1.3：P2 功能收尾
            _ensure_column(conn, "study_plans", "position_id", "position_id INTEGER")
            # v1.4：复盘报告补全总评/知识覆盖/学习路线（此前生成报告时丢失了这些字段）
            _ensure_column(conn, "reports", "summary", "summary TEXT NOT NULL DEFAULT ''")
            _ensure_column(conn, "reports", "coverage", "coverage JSON")
            _ensure_column(conn, "reports", "learning_path", "learning_path JSON")
            # v1.5：报告显式状态（pending/ready/fallback/failed），取代"占位总评"隐式判断
            _ensure_column(conn, "reports", "status", "status VARCHAR(20) NOT NULL DEFAULT 'pending'")
            # 旧数据修复：已有真实总评的历史报告视为 ready；占位报告保留 pending 等待补生成
            _pending_marker = "报告生成中，请稍后刷新查看…"
            conn.execute(
                text(
                    "UPDATE reports SET status = 'ready' "
                    "WHERE status = 'pending' AND summary IS NOT NULL AND summary != :marker"
                ).bindparams(marker=_pending_marker)
            )
            conn.commit()

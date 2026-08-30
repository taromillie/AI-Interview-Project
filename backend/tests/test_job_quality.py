# -*- coding: utf-8 -*-
"""岗位数据质量治理（方案③）单元测试：名称归一、技能规范与补全、存量清洗。"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models.position import Position
from app.services.job_crawler import JobItem
from app.services.job_quality import clean_job_item, reprocess_jobs
from app.services.skill_catalog import complete_skills


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()
    yield session
    session.close()
    engine.dispose()


def _item(name="Java开发", source="jobui", direction="backend", skills=None):
    return JobItem(
        name=name,
        direction=direction,
        difficulty="mid",
        skills=list(skills or []),
        company="A公司",
        city="北京",
        salary_min=15,
        salary_max=25,
        description="",
        welfare=[],
        source=source,
        source_id="id-1",
        source_url="",
        published_at=None,
    )


def _position(name, source="jobui", direction="tech", skills=None):
    return Position(
        name=name,
        company="A公司",
        direction=direction,
        difficulty="mid",
        skills=list(skills or []),
        salary_min=15,
        salary_max=25,
        is_public=True,
        status="active",
        source=source,
    )


# ───────────────────── clean_job_item ─────────────────────

def test_clean_job_item_normalizes_real_name():
    item = _item(name="高级Java开发工程师")
    clean_job_item(item)
    assert item.name == "Java开发"


def test_clean_job_item_keeps_builtin_name():
    """内置岗位名保持原样，保证按名去重 / 种子稳定。"""
    item = _item(name="Java 开发工程师", source="builtin")
    clean_job_item(item)
    assert item.name == "Java 开发工程师"


def test_clean_job_item_canonicalizes_skills():
    item = _item(name="Java开发", skills=["java", "golang", "MySQL", "Redis"])
    clean_job_item(item)
    assert item.skills == ["Java", "Go", "MySQL", "Redis"]


def test_clean_job_item_completes_sparse_skills():
    """技能稀疏（只有 [java]）的 Java 岗位补全为标准技能集，召回更精准。"""
    item = _item(name="Java开发", skills=["java"])
    clean_job_item(item)
    assert item.skills[0] == "Java"
    assert "Spring Boot" in item.skills
    assert len(item.skills) >= 4


def test_complete_skills_respects_rich_skills():
    """技能已 >=3 的岗位不强行补全，避免污染。"""
    skills = complete_skills("Java开发", "backend", ["Java", "MySQL", "Redis"])
    assert skills == ["Java", "MySQL", "Redis"]


# ───────────────────── reprocess_jobs ─────────────────────

def test_reprocess_jobs_normalizes_and_is_idempotent(db):
    db.add(_position("高级产品经理", direction="product", skills=["PRD", "需求分析"]))
    db.add(_position("资深算法工程师", direction="algorithm", skills=["python"]))
    db.commit()

    s1 = reprocess_jobs(db)
    assert s1["reprocessed"] == 2
    assert s1["changed"] == 2

    names = {p.name for p in db.query(Position).all()}
    assert names == {"产品经理", "算法"}

    # 幂等：第二次不再改动
    s2 = reprocess_jobs(db)
    assert s2["reprocessed"] == 2
    assert s2["changed"] == 0


def test_reprocess_jobs_skips_builtin(db):
    db.add(_position("后端开发工程师", source="builtin", skills=["Python", "Java", "MySQL", "Redis"]))
    db.commit()

    s = reprocess_jobs(db)
    assert s["reprocessed"] == 0
    assert s["changed"] == 0
    assert db.query(Position).first().name == "后端开发工程师"

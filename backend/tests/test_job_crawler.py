# -*- coding: utf-8 -*-
"""岗位同步测试：解析函数、_upsert 幂等、内置源同步去重。"""
import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models.position import Position
from app.services.job_crawler import (
    BuiltinSource,
    JobItem,
    JobuiSource,
    RemotiveSource,
    _clean_tags,
    _do_sync,
    _money_to_k,
    _parse_api_date,
    _upsert,
    build_description,
    default_skills,
    extract_skills,
    extract_welfare,
    infer_difficulty,
    infer_direction,
    parse_salary,
)


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    yield session
    session.close()


def make_item(**kw):
    base = dict(
        name="Python 后端工程师", direction="backend", difficulty="mid",
        skills=["Python"], company="某公司", city="北京",
        salary_min=15, salary_max=25, description="描述", welfare=["五险一金"],
        source="builtin", source_id=None, source_url="",
        published_at=datetime.datetime(2026, 8, 20),
    )
    base.update(kw)
    return JobItem(**base)


# ── 方向 / 难度推断 ──
class TestInfer:
    def test_direction_frontend(self):
        assert infer_direction("高级前端工程师 React") == "frontend"

    def test_direction_backend(self):
        assert infer_direction("Java 后端工程师") == "backend"

    def test_direction_fallback_tech(self):
        assert infer_direction("门店店长") == "tech"

    def test_difficulty_junior(self):
        assert infer_difficulty("1-3 年经验 初级") == "junior"

    def test_difficulty_senior(self):
        assert infer_difficulty("5 年以上架构经验") == "senior"

    def test_difficulty_mid(self):
        assert infer_difficulty("3-5 年经验") == "mid"


# ── 技能 / 福利 / 薪资解析 ──
class TestParse:
    def test_extract_skills_limit_and_dedup(self):
        skills = extract_skills("熟悉 python，会 Python、Java、Go、React、SQL", limit=3)
        assert len(skills) <= 3
        assert len(set(skills)) == len(skills)

    def test_extract_skills_empty(self):
        assert extract_skills("   ", limit=5) == []

    def test_extract_welfare(self):
        welfare = extract_welfare("五险一金、年终奖、免费三餐、弹性工作")
        assert "五险一金" in welfare
        assert "弹性工作" in welfare

    def test_parse_salary_k(self):
        assert parse_salary("15K-25K") == (15, 25)

    def test_parse_salary_wan(self):
        # 万元/年 → K/月（粗略 scale=10）
        assert parse_salary("20-30万/年") == (200, 300)

    def test_parse_salary_negotiable(self):
        assert parse_salary("面议") == (None, None)

    def test_parse_salary_14_month_dropped(self):
        # 14 薪是发薪月数，不是薪资上下限
        assert parse_salary("15K-25K·14薪") == (15, 25)

    def test_parse_salary_plain_yuan(self):
        assert parse_salary("15000-24000") == (15, 24)

    def test_default_skills_unknown_fallback(self):
        # 无对应方向时回退 tech 兜底技能，不为空
        assert default_skills("unknown") == default_skills("tech")

    def test_clean_tags_nested(self):
        tags = _clean_tags([["java"], " python ", ["后端"], None])
        assert "java" in tags
        assert "python" in tags
        assert "后端" in tags

    def test_money_to_k(self):
        assert _money_to_k(30000) == 30
        assert _money_to_k("5000") == 5000
        assert _money_to_k("abc") is None

    def test_parse_api_date_variants(self):
        assert _parse_api_date("2026-08-20") == datetime.datetime(2026, 8, 20)
        assert _parse_api_date("2026-08-20T10:00:00") == datetime.datetime(2026, 8, 20, 10, 0, 0)
        assert _parse_api_date("") is None

    def test_parse_relative_date(self):
        d = JobuiSource._parse_relative_date("3天前")
        assert d is not None
        assert (datetime.datetime.utcnow() - d).days == 3


# ── 方向推断与 _make_item ──
class TestMakeItem:
    def test_tech_direction_from_title(self):
        item = RemotiveSource()._make_item(
            name="Python 后端工程师", company="某公司", city="上海",
            url="https://x/job/1", source_id="1", tags=["python", "django"],
        )
        assert item is not None
        assert item.direction == "backend"
        assert item.source_id == "1"

    def test_non_tech_filtered_out(self):
        item = RemotiveSource()._make_item(
            name="门店店长", company="某公司", city="上海",
            url="https://x/job/2", source_id="2", tags=[],
        )
        assert item is None


# ── _upsert 幂等 ──
class TestUpsert:
    def test_insert_new(self, db):
        created = _upsert(db, make_item())
        assert created is True
        assert db.query(Position).count() == 1

    def test_builtin_dedup_by_name(self, db):
        assert _upsert(db, make_item(name="Python 后端工程师", source_id="a")) is True
        created2 = _upsert(db, make_item(name="Python 后端工程师", source_id="b"))
        assert created2 is False
        assert db.query(Position).count() == 1

    def test_source_id_dedup(self, db):
        it1 = make_item(name="A 公司后端", source="lagou", source_id="L-1")
        assert _upsert(db, it1) is True
        it2 = make_item(name="同名但不同展示", source="lagou", source_id="L-1")
        assert _upsert(db, it2) is False
        assert db.query(Position).count() == 1
        # 更新了名称
        assert db.query(Position).first().name == "同名但不同展示"

    def test_crawler_dedup_by_source_id_only(self, db):
        # 非内置源：同源不同 ID 的同名岗位视为不同岗位
        assert _upsert(db, make_item(name="某公司后端", source="lagou", source_id="L-1")) is True
        assert _upsert(db, make_item(name="某公司后端", source="lagou", source_id="L-2")) is True
        assert db.query(Position).count() == 2


# ── 内置源同步幂等 ──
class TestDoSync:
    def _stats(self):
        return {"sources": [], "total": 0, "new": 0, "updated": 0, "errors": 0}

    def test_builtin_sync_idempotent(self, db):
        stats1 = self._stats()
        _do_sync(db, "builtin", stats1)
        assert stats1["new"] >= 10  # 内置源固定数据
        count = db.query(Position).count()
        assert count == stats1["new"]

        stats2 = self._stats()
        _do_sync(db, "builtin", stats2)
        assert stats2["new"] == 0
        assert stats2["updated"] == count  # 二次同步全部命中更新
        assert db.query(Position).count() == count

    def test_builtin_source_fetch_count(self):
        jobs = BuiltinSource().fetch_jobs()
        assert len(jobs) >= 10
        assert all(j.source == "builtin" for j in jobs)

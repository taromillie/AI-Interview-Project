"""岗位方向聚合（岗位广场方向卡）单元测试。"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models.position import Position
from app.services.position_directions import build_directions, normalize_position_name


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()
    yield session
    session.close()
    engine.dispose()


# ───────────────────── 岗位名归一 ─────────────────────

@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("产品经理", "产品经理"),
        ("产品经理/高级产品经理", "产品经理"),
        ("产品经理/宠物药产品经理", "产品经理"),
        ("Java 开发工程师", "Java开发"),
        ("Java开发", "Java开发"),
        ("算法工程师", "算法"),
        ("推荐算法工程师", "推荐算法"),
        ("前端开发", "前端开发"),
        ("前端开发工程师", "前端开发"),
        ("前端架构工程师", "前端架构"),
        ("数据分析", "数据分析"),
        ("数据分析师", "数据分析"),
        ("运营专员", "运营"),
        ("AI 产品经理", "AI产品经理"),
        ("测试开发工程师", "测试开发"),
        # 职级前缀剥离
        ("高级产品经理", "产品经理"),
        ("资深算法工程师", "算法"),
        ("初级测试开发工程师", "测试开发"),
        ("高级Java开发工程师", "Java开发"),
        # 括号说明剥离
        ("产品经理（北京）", "产品经理"),
        ("算法工程师（大模型方向）", "算法"),
    ],
)
def test_normalize_position_name(raw, expected):
    assert normalize_position_name(raw) == expected


# ───────────────────── 方向聚合 ─────────────────────

def _mk(name, company, salary_min, salary_max, skills, **kw):
    return Position(
        name=name,
        company=company,
        direction=kw.get("direction", "tech"),
        difficulty=kw.get("difficulty", "mid"),
        skills=skills,
        salary_min=salary_min,
        salary_max=salary_max,
        is_public=True,
        status="active",
    )


def test_build_directions_groups_and_aggregates(db):
    db.add_all(
        [
            _mk("产品经理", "A公司", 15, 25, ["需求分析", "PRD", "数据分析"]),
            _mk("产品经理/高级产品经理", "B公司", 20, 35, ["需求分析", "PRD", "项目管理"]),
            _mk("AI 产品经理", "C公司", 25, 40, ["PRD", "大模型", "数据分析"]),
            _mk("Java开发", "D公司", 18, 30, ["Java", "Spring Boot", "MySQL"]),
            _mk("Java 开发工程师", "E公司", 15, 25, ["Java", "MySQL"]),
        ]
    )
    db.commit()

    dirs = build_directions(db.query(Position).all())
    by_key = {d["key"]: d for d in dirs}

    # 同族岗位（/ 变体、空格变体）归并为同一方向
    assert set(by_key) == {"产品经理", "AI产品经理", "Java开发"}
    assert by_key["产品经理"]["count"] == 2
    assert by_key["Java开发"]["count"] == 2

    # 展示名取多数派
    assert by_key["产品经理"]["name"] == "产品经理"
    assert by_key["Java开发"]["name"] == "Java开发"

    # 平均薪资
    assert by_key["产品经理"]["salary_min"] == 18  # (15+20)/2 = 17.5 → round 18
    assert by_key["产品经理"]["salary_max"] == 30  # (25+35)/2

    # Top 技能聚合
    assert "PRD" in by_key["产品经理"]["skills"]
    assert "Java" in by_key["Java开发"]["skills"]

    # 方向卡挂载岗位列表 + 首岗 id
    assert len(by_key["产品经理"]["positions"]) == 2
    assert by_key["产品经理"]["first_position_id"] == by_key["产品经理"]["positions"][0]["id"]

    # 按数量降序
    assert [d["key"] for d in dirs] == ["产品经理", "Java开发", "AI产品经理"]


def test_build_directions_merges_skill_case(db):
    """技能聚合大小写不敏感：java + Java 合并，显示计数更多者。"""
    db.add_all(
        [
            _mk("Java开发", "A公司", 15, 25, ["java", "Spring Boot"]),
            _mk("Java开发", "B公司", 15, 25, ["java"]),
            _mk("Java开发", "C公司", 15, 25, ["Java", "MySQL"]),
            _mk("Java开发", "D公司", 15, 25, ["Java", "JVM"]),
            _mk("Java开发", "E公司", 15, 25, ["Java", "Spring Cloud"]),
        ]
    )
    db.commit()

    dirs = build_directions(db.query(Position).all())
    d = dirs[0]
    # 大小写合并后只保留一个写法，且计数更多者（Java×3 > java×2）胜出
    assert d["skills"].count("java") + d["skills"].count("Java") == 1
    assert "Java" in d["skills"]
    assert "Spring Boot" in d["skills"]


def test_build_directions_handles_empty_skills_and_salary(db):
    db.add(_mk("后端开发工程师", "F公司", None, None, []))
    db.commit()

    dirs = build_directions(db.query(Position).all())
    assert len(dirs) == 1
    d = dirs[0]
    assert d["name"] == "后端开发工程师"
    assert d["count"] == 1
    assert d["skills"] == []
    assert d["salary_min"] is None
    assert d["salary_max"] is None

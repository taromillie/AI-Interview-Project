# -*- coding: utf-8 -*-
"""题库批量导入测试：JSON / Markdown 解析、auto 识别、去重落库。"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models.position import KnowledgeAtom, Position
from app.models.user import User
from app.services.question_import import (
    import_atoms,
    normalize_difficulty,
    parse_auto,
    parse_json,
    parse_markdown,
)


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    yield session
    session.close()


def make_user(db, username="tester"):
    user = User(username=username, password_hash="x")
    db.add(user)
    db.commit()
    return user


def make_position(db, name="后端工程师"):
    pos = Position(name=name)
    db.add(pos)
    db.commit()
    return pos


# ── 难度归一化 ──
class TestDifficulty:
    def test_valid(self):
        assert normalize_difficulty("senior") == "senior"
        assert normalize_difficulty("JUNIOR") == "junior"

    def test_invalid_fallback_mid(self):
        assert normalize_difficulty("expert") == "mid"
        assert normalize_difficulty("") == "mid"
        assert normalize_difficulty(None) == "mid"


# ── JSON 解析 ──
class TestParseJson:
    def test_top_level_array(self):
        items = parse_json('[{"question": "什么是闭包？", "tags": ["JS"], "difficulty": "senior"}]')
        assert items[0]["question"] == "什么是闭包？"
        assert items[0]["tags"] == ["JS"]
        assert items[0]["difficulty"] == "senior"

    def test_wrapped_object(self):
        items = parse_json('{"questions": [{"title": "解释一下 HTTPS"}]}')
        assert items[0]["question"] == "解释一下 HTTPS"

    def test_reference_points_list_and_string(self):
        items = parse_json(
            '[{"question": "q", "reference_points": ["a", "b"], "reference": "c"}]'
        )
        # reference_points 优先于 reference
        assert items[0]["reference_points"] == ["a", "b"]

    def test_missing_question_raises(self):
        with pytest.raises(ValueError, match="缺少 question"):
            parse_json('[{"tags": ["x"]}]')

    def test_bad_structure_raises(self):
        with pytest.raises(ValueError, match="数组"):
            parse_json('{"questions": "not-a-list"}')


# ── Markdown 解析 ──
class TestParseMarkdown:
    def test_heading_and_points(self):
        md = """## 什么是 TCP 三次握手？

- 第一次：客户端发送 SYN
- 第二次：服务端回复 SYN+ACK
- 第三次：客户端发送 ACK
"""
        items = parse_markdown(md)
        assert len(items) == 1
        assert items[0]["question"] == "什么是 TCP 三次握手？"
        assert len(items[0]["reference_points"]) == 3

    def test_tags_and_difficulty(self):
        md = """### Redis 持久化方式

- 标签: Redis, 中间件
- 难度: senior
- 要点: RDB 与 AOF 的区别
"""
        items = parse_markdown(md)
        assert items[0]["tags"] == ["Redis", "中间件"]
        assert items[0]["difficulty"] == "senior"
        assert items[0]["reference_points"] == ["RDB 与 AOF 的区别"]

    def test_multiple_headings(self):
        md = """## 第一题

- 要点一

## 第二题

- 要点二
"""
        items = parse_markdown(md)
        assert [i["question"] for i in items] == ["第一题", "第二题"]


# ── auto 识别 ──
class TestParseAuto:
    def test_json_detected(self):
        items = parse_auto('[{"question": "q1"}]')
        assert items[0]["question"] == "q1"

    def test_markdown_detected(self):
        items = parse_auto("## 标题题\n\n- 要点\n")
        assert items[0]["question"] == "标题题"


# ── 落库与去重 ──
class TestImportAtoms:
    def test_create_and_count(self, db):
        user = make_user(db)
        pos = make_position(db)
        items = [
            {"question": "q1", "reference_points": ["r1"], "tags": ["t1"], "difficulty": "mid"},
            {"question": "q2", "reference_points": [], "tags": [], "difficulty": "junior"},
        ]
        result = import_atoms(db, user, pos.id, items)
        assert result["created"] == 2
        assert result["skipped"] == 0
        assert result["errors"] == []
        assert db.query(KnowledgeAtom).filter_by(position_id=pos.id).count() == 2

    def test_duplicate_skipped(self, db):
        user = make_user(db)
        pos = make_position(db)
        items = [
            {"question": "q1", "reference_points": [], "tags": [], "difficulty": "mid"},
            {"question": "q1", "reference_points": [], "tags": [], "difficulty": "mid"},
            {"question": "q2", "reference_points": [], "tags": [], "difficulty": "mid"},
        ]
        result = import_atoms(db, user, pos.id, items)
        assert result["created"] == 2
        assert result["skipped"] == 1

    def test_empty_question_error_row(self, db):
        user = make_user(db)
        pos = make_position(db)
        result = import_atoms(db, user, pos.id, [{"question": "  ", "tags": []}])
        assert result["created"] == 0
        assert len(result["errors"]) == 1
        assert result["errors"][0]["reason"] == "题目为空"

    def test_missing_position_raises(self, db):
        user = make_user(db)
        with pytest.raises(ValueError, match="岗位不存在"):
            import_atoms(db, user, 999, [{"question": "q1", "tags": []}])

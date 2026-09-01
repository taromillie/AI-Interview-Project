# -*- coding: utf-8 -*-
"""用户数据隔离测试：他人资源一律 404，条件删除不影响他人数据。

盘点结论：所有按 id 操作的端点均已实现 owner 检查（越权统一 404）。
本文件以跨用户访问固化回归保障，防止未来改动引入越权。
"""
import json
import time
from typing import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from app.core.db import SessionLocal
from app.llm.base import LLMProvider
from app.main import app
from app.models.position import Position


class FakeLLM(LLMProvider):
    """按 prompt 关键词返回固定 JSON（简历解析 / 面试决策）。"""

    async def achat(self, messages, *, temperature=0.3, max_tokens=2048) -> str:
        text = messages[-1].content
        if "把下面的简历文本结构化" in text:
            return (
                '{"basic": {"name": "张三", "target_position": "后端开发", "years_of_exp": "3年"},'
                ' "education": ["本科"], "experience": ["A公司 后端开发"],'
                ' "projects": ["订单系统 高并发"],'
                ' "skills": ["Python", "FastAPI", "Redis"]}'
            )
        if "决策规则" in text:
            return (
                '{"action": "ask_question", "strategy": "project_probe",'
                ' "question": "请详细讲讲订单系统的架构设计？", "reason": "测试追问"}'
            )
        return '{"action": "finish", "strategy": "none", "question": "", "reason": "兜底"}'

    def stream(self, messages, *, temperature=0.7, max_tokens=2048) -> AsyncIterator[str]:
        async def gen():
            yield "ok"

        return gen()

    @property
    def name(self) -> str:
        return "fake-iso"


@pytest.fixture()
def fake_llm(monkeypatch):
    """替换 require_llm（简历解析 / 面试创建与进行均需要 LLM）。"""
    llm = FakeLLM()

    def _require(db, user):
        return llm

    monkeypatch.setattr("app.api.resume.require_llm", _require)
    monkeypatch.setattr("app.api.interview.require_llm", _require)
    return llm


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _register(client: TestClient, username: str) -> dict:
    client.post("/api/auth/register", json={"username": username, "password": "secret123"})
    token = client.post(
        "/api/auth/login", json={"username": username, "password": "secret123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def user_a(client: TestClient) -> dict:
    return _register(client, f"iso_a_{int(time.time())}")


@pytest.fixture(scope="module")
def user_b(client: TestClient) -> dict:
    return _register(client, f"iso_b_{int(time.time())}")


def _parse_sse(text: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    cur = None
    for line in text.splitlines():
        line = line.rstrip("\r")
        if not line.strip():
            cur = None
            continue
        if line.startswith("event:"):
            cur = line[len("event:"):].strip()
        elif line.startswith("data:"):
            if cur is not None:
                events.append((cur, json.loads(line[len("data:"):].strip())))
    return events


def test_resume_isolation(client: TestClient, user_a: dict, user_b: dict, fake_llm):
    """简历：他人不可读取/修改/删除，列表互不可见。"""
    resp = client.post(
        "/api/resumes/upload",
        data={"raw_text": "张三，3 年后端开发，熟悉 Python。"},
        headers=user_b,
    )
    assert resp.status_code == 200, resp.text
    rid = resp.json()["id"]

    assert client.get(f"/api/resumes/{rid}", headers=user_a).status_code == 404
    assert (
        client.put(
            f"/api/resumes/{rid}",
            data={"raw_text": "篡改内容：这是一段足够长的简历文本，用于通过校验。"},
            headers=user_a,
        ).status_code
        == 404
    )
    assert client.delete(f"/api/resumes/{rid}", headers=user_a).status_code == 404

    # 自己仍可访问，列表互不可见
    assert client.get(f"/api/resumes/{rid}", headers=user_b).status_code == 200
    ids_a = {r["id"] for r in client.get("/api/resumes", headers=user_a).json()}
    assert rid not in ids_a


def test_interview_isolation(client: TestClient, user_a: dict, user_b: dict, fake_llm):
    """面试：他人不可查看/开始/回答/结束。"""
    resp = client.post("/api/interviews", json={"mode": "text"}, headers=user_b)
    assert resp.status_code == 201, resp.text
    iid = resp.json()["id"]

    assert client.get(f"/api/interviews/{iid}", headers=user_a).status_code == 404
    assert client.post(f"/api/interviews/{iid}/start", headers=user_a).status_code == 404
    assert (
        client.post(
            f"/api/interviews/{iid}/answer", json={"content": "x"}, headers=user_a
        ).status_code
        == 404
    )
    assert client.post(f"/api/interviews/{iid}/finish", headers=user_a).status_code == 404


def test_report_isolation(client: TestClient, user_a: dict, user_b: dict, fake_llm):
    """报告：他人不可读取/重新生成/查状态。"""
    resp = client.post(
        "/api/interviews", json={"mode": "text", "max_rounds": 1}, headers=user_b
    )
    assert resp.status_code == 201, resp.text
    iid = resp.json()["id"]
    resp = client.post(f"/api/interviews/{iid}/finish", headers=user_b)
    assert resp.status_code == 200, resp.text
    report_id = resp.json()["report_id"]

    assert client.get(f"/api/reports/{report_id}", headers=user_a).status_code == 404
    assert (
        client.post(f"/api/reports/{report_id}/regenerate", headers=user_a).status_code == 404
    )
    assert (
        client.get(f"/api/reports/interviews/{iid}/status", headers=user_a).status_code == 404
    )
    assert client.get(f"/api/reports/{report_id}", headers=user_b).status_code == 200


def test_offer_isolation(client: TestClient, user_a: dict, user_b: dict):
    """Offer：他人不可修改/删除。"""
    resp = client.post(
        "/api/offers", json={"company": "某公司", "monthly_salary": 30000}, headers=user_b
    )
    assert resp.status_code in (200, 201), resp.text
    oid = resp.json()["id"]

    assert (
        client.put(f"/api/offers/{oid}", json={"company": "篡改"}, headers=user_a).status_code
        == 404
    )
    assert client.delete(f"/api/offers/{oid}", headers=user_a).status_code == 404
    # 列表互不可见
    ids_a = {o["id"] for o in client.get("/api/offers", headers=user_a).json()}
    assert oid not in ids_a


def test_jd_isolation(client: TestClient, user_a: dict, user_b: dict):
    """JD 导入：他人不可修改/删除。"""
    resp = client.post(
        "/api/jds",
        json={"title": "Python 开发", "content": "要求熟悉 FastAPI 与数据库设计，三年以上后端经验优先。"},
        headers=user_b,
    )
    assert resp.status_code in (200, 201), resp.text
    jid = resp.json()["id"]

    assert (
        client.put(
            f"/api/jds/{jid}",
            json={"title": "篡改标题", "content": "这是一段足够长的篡改内容，用于通过字段长度校验。"},
            headers=user_a,
        ).status_code
        == 404
    )
    assert client.delete(f"/api/jds/{jid}", headers=user_a).status_code == 404


def test_real_interview_isolation(client: TestClient, user_a: dict, user_b: dict):
    """真实面试复盘：他人不可查看/删除。"""
    resp = client.post(
        "/api/real-interview",
        json={"company": "某公司", "items": [{"question": "Q1"}]},
        headers=user_b,
    )
    assert resp.status_code in (200, 201), resp.text
    rid = resp.json()["id"]

    assert client.get(f"/api/real-interview/{rid}", headers=user_a).status_code == 404
    assert client.delete(f"/api/real-interview/{rid}", headers=user_a).status_code == 404


def test_interviewer_isolation(client: TestClient, user_a: dict, user_b: dict):
    """面试官角色：他人不可删除，本人可删除。"""
    resp = client.post("/api/interviewers", json={"name": "自定义考官"}, headers=user_b)
    assert resp.status_code in (200, 201), resp.text
    iid = resp.json()["id"]

    assert client.delete(f"/api/interviewers/{iid}", headers=user_a).status_code == 404
    assert client.delete(f"/api/interviewers/{iid}", headers=user_b).status_code == 204


def test_job_track_isolation(client: TestClient, user_a: dict, user_b: dict):
    """岗位收藏：A 取消收藏不影响 B 的收藏（条件删除）。"""
    with SessionLocal() as db:
        pos = Position(name="岗位隔离测试", skills=["Python"])
        db.add(pos)
        db.commit()
        pid = pos.id

    resp = client.post(f"/api/job-track/positions/{pid}/favorite", headers=user_b)
    assert resp.status_code in (200, 201), resp.text

    # A 取消收藏同一岗位 → 不删除 B 的收藏记录
    client.delete(f"/api/job-track/positions/{pid}/favorite", headers=user_a)

    summary_b = client.get("/api/job-track/summary", headers=user_b).json()
    assert pid in summary_b["favorite_ids"]

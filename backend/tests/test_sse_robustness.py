# -*- coding: utf-8 -*-
"""SSE 加固测试：服务异常时以 error 事件送达前端，连接不静默中断。

覆盖验收标准「面试断线可恢复」的服务端一半：
- AppError（业务错误）→ error 事件
- 未知异常（LLM/内部故障）→ error 事件（原实现会直接断流）
"""
import json
import time

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import AppError
from app.llm.base import LLMProvider
from app.main import app


class FakeLLM(LLMProvider):
    @property
    def name(self) -> str:
        return "fake-sse"

    async def achat(self, messages, *, temperature=0.3, max_tokens=2048) -> str:
        return json.dumps(
            {
                "action": "ask_question",
                "strategy": "probe",
                "question": "请讲讲 Redis 缓存？",
                "reason": "test",
            },
            ensure_ascii=False,
        )

    def stream(self, messages, *, temperature=0.7, max_tokens=2048):
        raise NotImplementedError


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def authed(client: TestClient) -> dict:
    username = f"sse_user_{int(time.time())}"
    client.post("/api/auth/register", json={"username": username, "password": "secret123"})
    token = client.post(
        "/api/auth/login", json={"username": username, "password": "secret123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def sse_llm(monkeypatch):
    llm = FakeLLM()
    monkeypatch.setattr("app.api.interview.require_llm", lambda db, user: llm)
    return llm


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


def _start_interview(client: TestClient, authed: dict) -> int:
    resp = client.post("/api/interviews", json={"mode": "text", "max_rounds": 3}, headers=authed)
    assert resp.status_code == 201, resp.text
    iid = resp.json()["id"]
    resp = client.post(f"/api/interviews/{iid}/start", headers=authed)
    assert resp.status_code == 200, resp.text
    return iid


def test_answer_app_error_yields_error_event(client, authed, sse_llm, monkeypatch):
    """业务错误（AppError）→ 200 + error 事件，而非中断连接。"""
    from app.services.interview_orchestrator import InterviewOrchestrator

    async def boom(self, content, request_id=None):
        raise AppError("面试官暂时不可用，请稍后重试")

    monkeypatch.setattr(InterviewOrchestrator, "answer", boom)

    iid = _start_interview(client, authed)
    resp = client.post(
        f"/api/interviews/{iid}/answer", json={"content": "我的回答"}, headers=authed
    )
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    assert events[0][0] == "thinking"
    assert events[-1][0] == "error"
    assert "不可用" in events[-1][1]["message"]


def test_answer_unexpected_error_yields_error_event(client, authed, sse_llm, monkeypatch):
    """未知异常（内部故障）→ 200 + error 事件，连接不静默中断。"""
    from app.services.interview_orchestrator import InterviewOrchestrator

    async def boom(self, content, request_id=None):
        raise RuntimeError("内部故障")

    monkeypatch.setattr(InterviewOrchestrator, "answer", boom)

    iid = _start_interview(client, authed)
    resp = client.post(
        f"/api/interviews/{iid}/answer", json={"content": "我的回答"}, headers=authed
    )
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    assert events[-1][0] == "error"
    assert "不可用" in events[-1][1]["message"]


def test_answer_request_id_passthrough(client, authed, sse_llm):
    """request_id 随 SSE 透传：正常回答仍返回 question 事件。"""
    iid = _start_interview(client, authed)
    resp = client.post(
        f"/api/interviews/{iid}/answer",
        json={"content": "我的回答", "request_id": "req-abc-123"},
        headers=authed,
    )
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    assert events[-1][0] == "question"

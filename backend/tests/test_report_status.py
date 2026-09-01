# -*- coding: utf-8 -*-
"""报告状态机测试：生成任务状态流转（ready/fallback/failed/跳过）与 regenerate 接口。

覆盖验收标准：
- 报告失败可识别（status=failed）
- 报告降级可识别（status=fallback，AI 不可用时不再伪装成 AI 报告）
- 失败/降级可重试（POST /reports/{id}/regenerate）
"""
import json
import tempfile
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.llm.base import LLMProvider
from app.main import app
from app.models.interview import Interview, InterviewMessage, Report
from app.models.position import Position
from app.models.user import User
from app.workers.report import generate_report_task

PENDING_SUMMARY = "报告生成中，请稍后刷新查看…"


class FakeReportLLM(LLMProvider):
    """报告生成用 LLM：fail=True 时抛异常。"""

    def __init__(self, fail: bool = False):
        self._fail = fail

    @property
    def name(self) -> str:
        return "fake-report"

    async def achat(self, messages, *, temperature=0.3, max_tokens=2048) -> str:
        if self._fail:
            raise RuntimeError("LLM 模拟失败")
        return json.dumps(
            {
                "overall_score": 80,
                "dimensions": {"tech": 80, "expression": 75, "logic": 82, "project": 70},
                "question_feedback": [
                    {"question": "q", "answer": "a", "score": 80, "comment": "回答完整"}
                ],
                "weak_points": ["项目细节不足"],
                "summary": "整体表现良好，建议补充量化指标。",
            },
            ensure_ascii=False,
        )

    def stream(self, messages, *, temperature=0.7, max_tokens=2048):
        raise NotImplementedError


@pytest.fixture()
def worker_db(monkeypatch):
    """临时文件库 + 替换报告 worker 的 SessionLocal，确保任务落在测试库中。

    不能用 :memory:（每连接独立数据库，后台任务新会话看不到测试会话写入的数据）。
    """
    engine = create_engine(
        f"sqlite:///{tempfile.mkdtemp(prefix='report_status_')}/t.db",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr("app.workers.report.SessionLocal", session)
    db = session()
    yield db
    db.close()


def _seed_interview(db, *, summary=PENDING_SUMMARY, status="pending"):
    user = User(username="worker_u", password_hash="x", email="w@example.com")
    pos = Position(name="Python 后端开发", skills=["Python"])
    db.add_all([user, pos])
    db.commit()
    db.refresh(user)
    db.refresh(pos)
    it = Interview(
        user_id=user.id,
        position_id=pos.id,
        difficulty="normal",
        max_rounds=1,
        status="reported",
        interview_type="normal",
        config={"target_position": "Python 后端开发"},
    )
    db.add(it)
    db.commit()
    db.refresh(it)
    db.add_all([InterviewMessage(interview_id=it.id, role="user", content="我的回答", strategy="answer")])
    db.commit()
    report = Report(interview_id=it.id, summary=summary, status=status)
    db.add(report)
    db.commit()
    db.refresh(report)
    return it, report


def test_worker_success_marks_ready(worker_db, monkeypatch):
    db = worker_db
    it, report = _seed_interview(db)
    monkeypatch.setattr("app.workers.report.get_llm_for_user", lambda d, uid: FakeReportLLM())

    generate_report_task(it.id)

    db.refresh(report)
    assert report.status == "ready"
    assert report.overall_score == 80
    assert report.summary != PENDING_SUMMARY
    db.refresh(it)
    assert it.status == "reported"


def test_worker_llm_failure_marks_fallback(worker_db, monkeypatch):
    db = worker_db
    it, report = _seed_interview(db)
    monkeypatch.setattr("app.workers.report.get_llm_for_user", lambda d, uid: FakeReportLLM(fail=True))

    generate_report_task(it.id)

    db.refresh(report)
    assert report.status == "fallback"
    assert report.summary  # 规则降级报告仍有总评


def test_worker_no_llm_marks_fallback(worker_db, monkeypatch):
    db = worker_db
    it, report = _seed_interview(db)
    monkeypatch.setattr("app.workers.report.get_llm_for_user", lambda d, uid: None)

    generate_report_task(it.id)

    db.refresh(report)
    assert report.status == "fallback"


def test_worker_unexpected_error_marks_failed(worker_db, monkeypatch):
    db = worker_db
    it, report = _seed_interview(db)
    monkeypatch.setattr("app.workers.report.get_llm_for_user", lambda d, uid: FakeReportLLM(fail=True))

    def boom(messages):
        raise RuntimeError("规则降级也失败")

    monkeypatch.setattr("app.workers.report.fallback_report", boom)

    generate_report_task(it.id)

    db.refresh(report)
    assert report.status == "failed"


def test_worker_skips_when_result_exists(worker_db, monkeypatch):
    db = worker_db
    it, report = _seed_interview(db, summary="已有真实总评", status="ready")
    monkeypatch.setattr("app.workers.report.get_llm_for_user", lambda d, uid: FakeReportLLM(fail=True))

    generate_report_task(it.id)

    db.refresh(report)
    assert report.status == "ready"
    assert report.summary == "已有真实总评"


# ------------------------- regenerate 接口（API 级） -------------------------


class FakeInterviewLLM(LLMProvider):
    """面试 + 报告两用 FakeLLM：决策走 ask_question，复盘 prompt 返回合法报告 JSON。"""

    @property
    def name(self) -> str:
        return "fake-interview"

    async def achat(self, messages, *, temperature=0.3, max_tokens=2048) -> str:
        text = messages[-1].content
        if "决策规则" in text:
            return json.dumps(
                {
                    "action": "ask_question",
                    "strategy": "project_probe",
                    "question": "请详细讲讲订单系统的架构设计？",
                    "reason": "测试追问",
                },
                ensure_ascii=False,
            )
        if "复盘" in text:
            return json.dumps(
                {
                    "overall_score": 82,
                    "dimensions": {"tech": 82, "expression": 76, "logic": 83, "project": 72},
                    "question_feedback": [
                        {"question": "q", "answer": "a", "score": 82, "comment": "回答完整"}
                    ],
                    "weak_points": ["项目细节不足"],
                    "summary": "AI 重新生成：整体表现良好，建议补充量化指标。",
                },
                ensure_ascii=False,
            )
        return json.dumps(
            {"action": "finish", "strategy": "none", "question": "", "reason": "兜底"},
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
    username = f"report_user_{int(time.time())}"
    client.post("/api/auth/register", json={"username": username, "password": "secret123"})
    resp = client.post("/api/auth/login", json={"username": username, "password": "secret123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def interview_llm(monkeypatch):
    """替换面试 API 层 require_llm。报告 worker 的 get_llm_for_user 不替换（→ None → fallback）。"""
    llm = FakeInterviewLLM()

    def _require(db, user):
        return llm

    monkeypatch.setattr("app.api.interview.require_llm", _require)
    return llm


def _parse_sse(text: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    cur_event = None
    for line in text.splitlines():
        line = line.rstrip("\r")
        if not line.strip():
            cur_event = None
            continue
        if line.startswith("event:"):
            cur_event = line[len("event:"):].strip()
        elif line.startswith("data:"):
            if cur_event is not None:
                events.append((cur_event, json.loads(line[len("data:"):].strip())))
    return events


def _finish_interview(client: TestClient, authed: dict) -> tuple[int, int]:
    """创建并完成一场 1 轮面试，返回 (interview_id, report_id)。"""
    resp = client.post(
        "/api/interviews",
        json={"mode": "text", "max_rounds": 1},
        headers=authed,
    )
    assert resp.status_code == 201, resp.text
    interview_id = resp.json()["id"]

    resp = client.post(f"/api/interviews/{interview_id}/start", headers=authed)
    assert resp.status_code == 200, resp.text

    resp = client.post(
        f"/api/interviews/{interview_id}/answer",
        json={"content": "我的回答内容，包含具体实现。"},
        headers=authed,
    )
    assert resp.status_code == 200, resp.text
    events = _parse_sse(resp.text)
    last = events[-1]
    assert last[0] == "finished"
    return interview_id, last[1]["report_id"]


def test_regenerate_full_flow(client: TestClient, authed: dict, interview_llm, monkeypatch):
    """无 LLM → fallback → 提供 LLM 后 regenerate → ready；他人不可操作；ready 后可再次重新生成。"""
    interview_id, report_id = _finish_interview(client, authed)

    # 无 LLM 配置 → 报告应为 fallback（可识别降级）
    deadline = time.time() + 5
    report = None
    while time.time() < deadline:
        resp = client.get(f"/api/reports/{report_id}", headers=authed)
        report = resp.json()
        if report.get("status") == "fallback":
            break
        time.sleep(0.05)
    else:
        pytest.fail(f"报告应降级为 fallback，实际 {report and report.get('status')}")

    # 他人不可重新生成（数据隔离）
    other_user = f"report_other_{int(time.time())}"
    client.post("/api/auth/register", json={"username": other_user, "password": "secret123"})
    other_token = client.post(
        "/api/auth/login", json={"username": other_user, "password": "secret123"}
    ).json()["access_token"]
    resp = client.post(
        f"/api/reports/{report_id}/regenerate",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.status_code == 404

    # 提供可用 LLM 后 regenerate → 重新生成成功
    monkeypatch.setattr(
        "app.workers.report.get_llm_for_user", lambda d, uid: FakeInterviewLLM()
    )
    resp = client.post(f"/api/reports/{report_id}/regenerate", headers=authed)
    assert resp.status_code == 202, resp.text
    assert resp.json()["status"] == "processing"

    # 后台任务在 TestClient 中同步执行完成 → 直接拉取确认 ready
    resp = client.get(f"/api/reports/{report_id}", headers=authed)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"
    assert "AI 重新生成" in resp.json()["summary"]

    # 状态端点同样反映 ready
    st = client.get(f"/api/reports/interviews/{interview_id}/status", headers=authed).json()
    assert st["status"] == "reported"

    # ready 后仍允许重新生成（用于刷新逐题优化建议等）
    resp = client.post(f"/api/reports/{report_id}/regenerate", headers=authed)
    assert resp.status_code == 202
    assert resp.json()["status"] == "processing"

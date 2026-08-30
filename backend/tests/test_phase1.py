"""Phase 1（MVP 闭环）集成测试：简历诊断 → 文字面试 → 复盘报告。

使用 FakeLLM 替换 require_llm，走真实 HTTP 链路（含 SSE），不依赖真实大模型。
"""
import json
import time

import pytest
from fastapi.testclient import TestClient
from typing import AsyncIterator

from app.llm.base import ChatMessage, LLMProvider
from app.main import app


class FakeLLM(LLMProvider):
    """按 prompt 关键词返回固定 JSON，模拟 LLM 各环节输出。"""

    async def achat(self, messages, *, temperature=0.3, max_tokens=2048) -> str:
        text = messages[-1].content
        if "【JD 内容】" in text:
            return '{"required": ["Python", "MySQL", "FastAPI"], "bonus": ["Docker"]}'
        if "把下面的简历文本结构化" in text:
            return (
                '{"basic": {"name": "张三", "target_position": "后端开发", "years_of_exp": "3年"},'
                ' "education": ["本科"], "experience": ["A公司 后端开发"],'
                ' "projects": ["订单系统 高并发"],'
                ' "skills": ["Python", "FastAPI", "Redis"]}'
            )
        if "简历优化建议" in text:
            return '["补充 MySQL 实战项目", "量化系统性能指标"]'
        if "决策规则" in text:
            return (
                '{"action": "ask_question", "strategy": "project_probe",'
                ' "question": "请详细讲讲订单系统的架构设计？", "reason": "测试追问"}'
            )
        if "复盘" in text:
            return (
                '{"overall_score": 80,'
                ' "dimensions": {"tech": 80, "expression": 75, "logic": 82, "project": 70},'
                ' "question_feedback": [{"question": "q", "answer": "a", "score": 80, "comment": "回答完整"}],'
                ' "weak_points": ["项目细节不足"], "summary": "整体表现良好，建议补充量化指标。"}'
            )
        return '{"action": "finish", "strategy": "none", "question": "", "reason": "兜底"}'

    def stream(self, messages, *, temperature=0.7, max_tokens=2048) -> AsyncIterator[str]:
        async def gen():
            yield "ok"

        return gen()

    @property
    def name(self) -> str:
        return "fake"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def authed(client: TestClient) -> dict:
    """注册并返回带 token 的请求头。"""
    username = "phase1_user"
    client.post(
        "/api/auth/register",
        json={"username": username, "password": "secret123"},
    )
    resp = client.post(
        "/api/auth/login",
        json={"username": username, "password": "secret123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def fake_llm(monkeypatch):
    """替换 API 层 require_llm 为 FakeLLM。"""
    llm = FakeLLM()

    def _require(db, user):
        return llm

    monkeypatch.setattr("app.api.resume.require_llm", _require)
    monkeypatch.setattr("app.api.interview.require_llm", _require)
    return llm


def _parse_sse(text: str) -> list[tuple[str, dict]]:
    """解析 SSE 响应文本为 [(event, data), ...]（兼容 CRLF/LF 分隔）。"""
    events: list[tuple[str, dict]] = []
    cur_event = None
    for line in text.splitlines():
        line = line.rstrip("\r")
        if not line.strip():
            cur_event = None
            continue
        if line.startswith("event: "):
            cur_event = line[7:].strip()
        elif line.startswith("data: "):
            if cur_event is not None:
                events.append((cur_event, json.loads(line[6:])))
                cur_event = None
    return events


def test_upload_and_diagnose(client: TestClient, authed: dict, fake_llm):
    """简历上传 + 简历×JD 诊断。"""
    # 上传（粘贴文本）
    resp = client.post(
        "/api/resumes/upload",
        data={"raw_text": "张三，3年后端开发，熟悉 Python、FastAPI、Redis，做过订单系统。"},
        headers=authed,
    )
    assert resp.status_code == 200, resp.text
    resume = resp.json()
    assert resume["id"] > 0
    assert "Python" in resume["skills"]

    # 诊断
    resp = client.post(
        "/api/resumes/diagnose",
        json={"jd_text": "招聘后端开发工程师，要求熟练掌握 Python、MySQL、FastAPI，熟悉 Docker 优先。"},
        headers=authed,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["diagnostic_id"] > 0
    assert 0 <= data["match_score"] <= 100
    assert any("MySQL" in g["skill"] for g in data["gaps"])  # 简历缺 MySQL
    assert data["resume_suggestions"]


def test_resume_upload_requires_input(client: TestClient, authed: dict):
    """无任何输入时上传应报 400。"""
    resp = client.post("/api/resumes/upload", data={}, headers=authed)
    assert resp.status_code == 400


def test_interview_full_flow(client: TestClient, authed: dict, fake_llm):
    """面试创建 → 开始 → 回答 → 结束 → 报告全链路。"""
    # 先上传简历
    resp = client.post(
        "/api/resumes/upload",
        data={"raw_text": "张三，3年后端开发，熟悉 Python、FastAPI、Redis。"},
        headers=authed,
    )
    resume_id = resp.json()["id"]

    # 创建面试（3 轮）
    resp = client.post(
        "/api/interviews",
        json={"resume_id": resume_id, "mode": "text", "max_rounds": 3},
        headers=authed,
    )
    assert resp.status_code == 201, resp.text
    interview = resp.json()
    interview_id = interview["id"]

    # 开始 → 拿到开场问题
    resp = client.post(f"/api/interviews/{interview_id}/start", headers=authed)
    assert resp.status_code == 200, resp.text
    events = _parse_sse(resp.text)
    assert events[0][0] == "preparing"
    assert events[1][0] == "question"
    assert events[1][1]["question"]
    assert events[1][1]["finished"] is False

    # 回答 3 轮 → 达到轮数上限自动结束并生成报告
    report_id = None
    for i in range(3):
        resp = client.post(
            f"/api/interviews/{interview_id}/answer",
            json={"content": f"我的回答第 {i + 1} 条，包含具体实现细节。"},
            headers=authed,
        )
        assert resp.status_code == 200, resp.text
        events = _parse_sse(resp.text)
        assert events[0][0] == "thinking"
        last = events[-1]
        if last[0] == "finished":
            report_id = last[1]["report_id"]
            break
        assert last[0] == "question"
        assert last[1]["question"]

    # 到 3 轮上限应已结束
    assert report_id is not None, "达到轮数上限后应自动结束并生成报告"

    # 报告由后台线程生成：轮询状态接口等待完成（与前端轮询一致），避免竞态
    deadline = time.time() + 10
    while time.time() < deadline:
        st = client.get(
            f"/api/reports/interviews/{interview_id}/status", headers=authed
        ).json()
        if st.get("status") == "reported":
            break
        time.sleep(0.1)
    else:
        pytest.fail("等待报告生成超时")

    # 查报告
    resp = client.get(f"/api/reports/{report_id}", headers=authed)
    assert resp.status_code == 200, resp.text
    report = resp.json()
    assert 0 <= report["overall_score"] <= 100
    assert set(report["dimensions"].keys()) >= {"tech", "expression", "logic", "project"}
    assert isinstance(report["question_feedback"], list)


def test_interview_ownership(client: TestClient, authed: dict, fake_llm):
    """他人面试/报告不可访问。"""
    # 第二个用户
    resp = client.post(
        "/api/auth/register",
        json={"username": "phase1_other", "password": "secret123"},
    )
    other_token = client.post(
        "/api/auth/login",
        json={"username": "phase1_other", "password": "secret123"},
    ).json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    resp = client.post("/api/interviews", json={}, headers=other_headers)
    assert resp.status_code == 201
    other_interview_id = resp.json()["id"]

    # 第一个用户不可结束第二个用户的面试 → 404
    resp = client.post(f"/api/interviews/{other_interview_id}/finish", headers=authed)
    assert resp.status_code == 404

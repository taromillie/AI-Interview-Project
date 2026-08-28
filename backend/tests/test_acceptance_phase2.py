"""工作包 B 验收测试：业务接口、状态流转和异步报告。"""
import time

import pytest
from fastapi.testclient import TestClient

from app.llm.base import ChatMessage, LLMProvider
from app.models.interview import Interview
from app.workers.report import generate_report_task


class FakeLLM(LLMProvider):
    async def achat(self, messages: list[ChatMessage], *, temperature=0.3, max_tokens=2048) -> str:
        text = messages[-1].content
        if "复盘" in text:
            return '{"overall_score": 80, "dimensions": {"tech": 80, "expression": 75, "logic": 82, "project": 70}, "question_feedback": [], "weak_points": ["项目细节不足"], "summary": "整体表现良好。"}'
        if "转行" in text:
            return '{"transferable": [{"skill": "Python", "evidence": "项目经验"}], "gaps": [], "roadmap": [], "transition_projects": [], "summary": "可迁移。"}'
        if "谈薪" in text:
            return '{"salary_range": [15, 20, 25], "factors": ["经验"], "strategy": ["量化成果"]}'
        if "备战" in text:
            return '{"title": "后端备战", "tasks": [{"day": 1, "done": false}], "summary": "按计划复习。"}'
        return '{"action": "ask_question", "strategy": "deep_dive", "question": "请介绍项目？", "reason": "测试"}'

    @property
    def name(self) -> str:
        return "fake"

    def stream(self, messages: list[ChatMessage], *, temperature=0.7, max_tokens=2048):
        async def generator():
            yield "ok"
        return generator()


@pytest.fixture()
def fake_llm(monkeypatch):
    llm = FakeLLM()

    def provide(db, user):
        return llm

    for module in ("career", "salary", "study_plan", "interview"):
        monkeypatch.setattr(f"app.api.{module}.require_llm", provide)
    monkeypatch.setattr("app.workers.report.get_llm_for_user", lambda db, user_id: llm)
    return llm


@pytest.fixture(scope="module")
def phase2_client():
    from app.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="module")
def phase2_auth(phase2_client: TestClient):
    username = f"phase2_{int(time.time())}"
    response = phase2_client.post(
        "/api/auth/register", json={"username": username, "password": "secret123"}
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_career_salary_and_study_interfaces(phase2_client, phase2_auth, fake_llm):
    career = phase2_client.post(
        "/api/career/diagnosis",
        json={"from_position": "测试开发", "to_position": "后端开发"},
        headers=phase2_auth,
    )
    assert career.status_code == 200
    assert {"transferable", "gaps", "roadmap"} <= career.json().keys()

    salary = phase2_client.post(
        "/api/salary/evaluate",
        json={"skill_stack": ["Python"], "years": 3, "city": "上海", "target_position": "后端开发"},
        headers=phase2_auth,
    )
    assert salary.status_code == 200
    assert len(salary.json()["salary_range"]) == 3

    study = phase2_client.post(
        "/api/study-plan/generate",
        json={"target_position": "后端开发", "days": 7},
        headers=phase2_auth,
    )
    assert study.status_code == 200
    assert study.json()["days"] == 7


def test_interviewer_and_difficulty_are_persisted(phase2_client, phase2_auth, fake_llm):
    interviewers = phase2_client.get("/api/interviewers", headers=phase2_auth)
    assert interviewers.status_code == 200
    interviewer_id = interviewers.json()[0]["id"] if interviewers.json() else None
    payload = {"target_position": "后端开发", "difficulty": "hard", "max_rounds": 1}
    if interviewer_id:
        payload["interviewer_id"] = interviewer_id
    response = phase2_client.post("/api/interviews", json=payload, headers=phase2_auth)
    assert response.status_code == 201
    data = response.json()
    assert data["difficulty"] == "hard"
    if interviewer_id:
        assert data["interviewer_id"] == interviewer_id


def test_knowledge_atom_status_flow(phase2_client, phase2_auth):
    positions = phase2_client.get("/api/questions/positions", headers=phase2_auth)
    assert positions.status_code == 200, positions.text
    if not positions.json():
        pytest.skip("题库岗位为空")
    response = phase2_client.post(
        "/api/questions",
        params=[
            ("position_id", str(positions.json()[0]["id"])),
            ("question", "如何设计单元测试"),
            ("tags", "Python"),
        ],
        headers=phase2_auth,
    )
    if response.status_code == 403:
        pytest.skip("当前测试用户不是管理员")
    assert response.status_code in (200, 201)
    atom_id = response.json()["id"]
    assert response.json()["status"] == "draft"
    published = phase2_client.post(f"/api/questions/{atom_id}/publish", headers=phase2_auth)
    assert published.status_code == 403


def test_async_report_task_and_status(phase2_client, phase2_auth, fake_llm):
    response = phase2_client.post(
        "/api/interviews", json={"target_position": "后端开发", "max_rounds": 1}, headers=phase2_auth
    )
    assert response.status_code == 201
    interview_id = response.json()["id"]
    queued = phase2_client.post(f"/api/reports/interviews/{interview_id}/generate", headers=phase2_auth)
    assert queued.status_code == 202
    started = time.perf_counter()
    generate_report_task(interview_id)
    assert time.perf_counter() - started < 60
    status = phase2_client.get(f"/api/reports/interviews/{interview_id}/status", headers=phase2_auth)
    assert status.status_code == 200
    assert status.json()["status"] == "reported"

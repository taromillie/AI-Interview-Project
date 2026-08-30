# -*- coding: utf-8 -*-
"""岗位收藏与投递跟踪 API 测试：幂等、状态流转、非法输入、404。"""
import pytest
from fastapi.testclient import TestClient

from app.core.db import SessionLocal
from app.main import app
from app.models.position import Position

TEST_USERNAME = "track_tester"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def token(client: TestClient) -> str:
    resp = client.post(
        "/api/auth/register",
        json={"username": TEST_USERNAME, "password": "secret123"},
    )
    assert resp.status_code in (200, 201)
    return resp.json()["access_token"]


@pytest.fixture(scope="module")
def position_id() -> int:
    with SessionLocal() as db:
        pos = Position(
            name="测试后端工程师",
            direction="backend",
            difficulty="mid",
            skills=["Python"],
            company="测试公司",
            city="北京",
            salary_min=15,
            salary_max=25,
            description="职责描述",
            welfare=["五险一金"],
            source="builtin",
            source_id="track_test_1",
        )
        db.add(pos)
        db.commit()
        return pos.id


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── 收藏 ──
class TestFavorite:
    def test_favorite_and_summary(self, client, token, position_id):
        resp = client.post(f"/api/job-track/positions/{position_id}/favorite", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["favorite"] is True

        # 幂等：重复收藏仍 200
        resp = client.post(f"/api/job-track/positions/{position_id}/favorite", headers=_auth(token))
        assert resp.status_code == 200

        summary = client.get("/api/job-track/summary", headers=_auth(token)).json()
        assert position_id in summary["favorite_ids"]

    def test_unfavorite(self, client, token, position_id):
        resp = client.delete(f"/api/job-track/positions/{position_id}/favorite", headers=_auth(token))
        assert resp.status_code == 200
        summary = client.get("/api/job-track/summary", headers=_auth(token)).json()
        assert position_id not in summary["favorite_ids"]

    def test_favorite_missing_position_404(self, client, token):
        resp = client.post("/api/job-track/positions/999999/favorite", headers=_auth(token))
        assert resp.status_code == 404


# ── 投递跟踪 ──
class TestApplication:
    def test_set_and_update_status(self, client, token, position_id):
        resp = client.put(
            f"/api/job-track/positions/{position_id}/application",
            params={"status": "applied", "note": "已投递"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["application"]["status"] == "applied"

        # 状态流转：applied -> interviewing（upsert 更新同一行）
        resp = client.put(
            f"/api/job-track/positions/{position_id}/application",
            params={"status": "interviewing"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["application"]["status"] == "interviewing"

        summary = client.get("/api/job-track/summary", headers=_auth(token)).json()
        assert summary["applications"][str(position_id)]["status"] == "interviewing"

    def test_invalid_status_422(self, client, token, position_id):
        resp = client.put(
            f"/api/job-track/positions/{position_id}/application",
            params={"status": "unknown"},
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_remove_application(self, client, token, position_id):
        resp = client.delete(
            f"/api/job-track/positions/{position_id}/application",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        summary = client.get("/api/job-track/summary", headers=_auth(token)).json()
        assert str(position_id) not in summary["applications"]

    def test_application_missing_position_404(self, client, token):
        resp = client.put(
            "/api/job-track/positions/999999/application",
            params={"status": "applied"},
            headers=_auth(token),
        )
        assert resp.status_code == 404

"""冒烟测试：认证链路与健康检查。"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    # with 上下文会触发 FastAPI lifespan（建表等启动逻辑）
    with TestClient(app) as c:
        yield c


def test_health(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_login_flow(client: TestClient):
    username = "test_user"
    resp = client.post(
        "/api/auth/register",
        json={"username": username, "password": "secret123"},
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]

    # 携带 token 访问 /me
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == username

    # 登录
    resp = client.post(
        "/api/auth/login",
        json={"username": username, "password": "secret123"},
    )
    assert resp.status_code == 200

    # 未登录访问受保护接口 → 401
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401

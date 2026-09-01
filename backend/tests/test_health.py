# -*- coding: utf-8 -*-
"""健康检查测试：存活端点不依赖外部，就绪端点验证数据库连通。"""
from fastapi.testclient import TestClient

from app.main import app


def test_health_live():
    with TestClient(app) as client:
        resp = client.get("/health/live")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["app"]


def test_health_ready():
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"
    assert data["app"]
    assert data["version"]

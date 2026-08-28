"""FastAPI 应用入口。"""
import logging
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import SessionLocal, init_db
from app.core.exceptions import register_exception_handlers

logger = logging.getLogger(__name__)


def _job_sync_loop() -> None:
    """后台岗位同步线程：每 60 秒检查一次是否到达同步时间（间隔可动态调整）。"""
    from app.services.job_crawler import sync_jobs
    from app.services.sync_state import is_sync_due

    while True:
        try:
            if is_sync_due():
                logger.info("定时岗位同步开始（动态间隔模式）")
                sync_jobs()
        except Exception as exc:  # noqa: BLE001 采集失败只记录日志
            logger.warning("定时岗位同步失败: %s", exc)
        time.sleep(60.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库表结构（开发用；生产走 Alembic）
    init_db()
    # 启动后台岗位同步线程
    if settings.JOB_SYNC_ON_STARTUP:
        worker = threading.Thread(target=_job_sync_loop, daemon=True, name="job-sync")
        worker.start()
        logger.info("岗位同步后台线程已启动（间隔可动态调整，初始 %.1f 小时）", settings.JOB_SYNC_INTERVAL_HOURS)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI 模拟面试官与职业规划系统 API",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


# 路由注册
from app.api import (  # noqa: E402
    auth,
    career,
    interview,
    interviewer,
    jd,
    offer,
    profile,
    provider,
    question,
    real_interview,
    report,
    resume,
    salary,
    study_plan,
)

for router in (
    auth.router,
    provider.router,
    resume.router,
    jd.router,
    profile.router,
    interview.router,
    interviewer.router,
    report.router,
    career.router,
    salary.router,
    question.router,
    study_plan.router,
    real_interview.router,
    offer.router,
):
    app.include_router(router, prefix="/api")

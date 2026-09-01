"""FastAPI 应用入口。"""
import logging
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse

from sqlalchemy import text

from app.core.config import settings
from app.core.db import SessionLocal, init_db
from app.core.exceptions import register_exception_handlers
from app.core.logging_config import setup_logging
from app.core.rate_limit import limiter

setup_logging(settings.LOG_LEVEL)

logger = logging.getLogger(__name__)


def _job_sync_loop(stop_event: threading.Event) -> None:
    """后台岗位同步线程：每 60 秒检查一次是否到达同步时间（间隔可动态调整）。

    使用 stop_event.wait 代替 sleep，应用停机时可被优雅中断，
    不会在请求已结束时继续占用数据库连接。
    """
    from app.services.job_crawler import sync_jobs
    from app.services.sync_state import is_sync_due

    while not stop_event.wait(60.0):
        try:
            if is_sync_due():
                logger.info("定时岗位同步开始（动态间隔模式）")
                sync_jobs()
        except Exception as exc:  # noqa: BLE001 采集失败只记录日志
            logger.warning("定时岗位同步失败: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库表结构（开发用；生产走 Alembic）
    init_db()
    # 启动后台岗位同步线程
    stop_event = threading.Event()
    if settings.JOB_SYNC_ON_STARTUP:
        worker = threading.Thread(
            target=_job_sync_loop, args=(stop_event,), daemon=True, name="job-sync"
        )
        worker.start()
        logger.info("岗位同步后台线程已启动（间隔可动态调整，初始 %.1f 小时）", settings.JOB_SYNC_INTERVAL_HOURS)
    try:
        yield
    finally:
        # 优雅停机：最多等待 2 秒让同步线程退出当前周期
        if settings.JOB_SYNC_ON_STARTUP:
            stop_event.set()
            worker.join(timeout=2)
            logger.info("岗位同步后台线程已停止")


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

# 限流：绑定到 app 并提供统一的 429 响应
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "detail": "请求过于频繁，请稍后再试",
            "limit": str(exc.detail) if exc.detail else "rate limit exceeded",
        },
    )


@app.middleware("http")
async def request_logging(request: Request, call_next):
    """结构化请求日志：方法、路径、状态码、耗时、客户端 IP。"""
    if not request.url.path.startswith("/api"):
        return await call_next(request)
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1fms, ip=%s)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request.client.host if request.client else "-",
    )
    return response


app.add_middleware(SlowAPIMiddleware)


@app.get("/health/live", tags=["system"])
def health_live() -> dict:
    """存活检查：进程在即通过，不探测依赖，供容器 liveness 使用。"""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health", tags=["system"])
def health() -> dict:
    """就绪检查：包含数据库连通性探测，供容器 readiness 与部署验证使用。"""
    db_ok = True
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("健康检查：数据库连接异常: %s", exc)
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "ok" if db_ok else "error",
    }


# 路由注册
from app.api import (  # noqa: E402
    auth,
    career,
    interview,
    interviewer,
    jd,
    job_track,
    offer,
    position_match,
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
    position_match.router,
    job_track.router,
):
    app.include_router(router, prefix="/api")

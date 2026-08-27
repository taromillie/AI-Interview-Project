"""FastAPI 应用入口。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import init_db
from app.core.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库表结构（开发用；生产走 Alembic）
    init_db()
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
from app.api import auth, career, interview, jd, profile, provider, question, report, resume, salary  # noqa: E402

for router in (
    auth.router,
    provider.router,
    resume.router,
    jd.router,
    profile.router,
    interview.router,
    report.router,
    career.router,
    salary.router,
    question.router,
):
    app.include_router(router, prefix="/api")

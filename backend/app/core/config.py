"""应用配置：环境变量加载（pydantic-settings）。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用
    APP_NAME: str = "AI 模拟面试官与职业规划系统"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # 数据库
    DATABASE_URL: str = "sqlite:///./app.db"

    # 向量库（可选增强：未配置 Embedding 时自动降级为关键词检索）
    VECTOR_DB_PATH: str = "./data/chroma"
    VECTOR_COLLECTION: str = "knowledge_atoms"
    EMBEDDING_ENABLED: bool = False
    EMBEDDING_BASE_URL: str = ""        # OpenAI 兼容地址，如 https://api.openai.com/v1
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_TIMEOUT: int = 30

    # 安全
    JWT_SECRET: str = "please-change-this-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天
    AES_KEY: str = "please-change-this-aes-key-32bytes!"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # 默认模型（用户未配置时的回退）
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
    DEFAULT_LLM_BASE_URL: str = "https://api.openai.com/v1"

    # 岗位采集
    JOB_SOURCE_ENABLED: str = "jobui"    # 逗号分隔: jobui(职友集真实数据) / builtin(离线示例兜底，默认关闭)
    JOB_SYNC_INTERVAL_HOURS: float = 0.5  # 默认自动同步间隔（小时，0.5=30分钟；可在前端动态调整）
    JOB_SYNC_ON_STARTUP: bool = True      # 启动后立即同步一次


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

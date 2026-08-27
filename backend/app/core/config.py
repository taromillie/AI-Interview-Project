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

    # 向量库
    VECTOR_DB_PATH: str = "./data/chroma"
    EMBEDDING_MODEL: str = "BAAI/bge-m3"

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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

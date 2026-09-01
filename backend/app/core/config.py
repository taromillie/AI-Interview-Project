"""应用配置：环境变量加载（pydantic-settings）。"""
import logging
from functools import lru_cache
from warnings import warn

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# 默认开发密钥（仅用于本地开发，生产环境必须替换）
DEFAULT_JWT_SECRET = "please-change-this-secret"
DEFAULT_AES_KEY = "please-change-this-aes-key-32bytes!"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用
    APP_NAME: str = "AI 模拟面试官与职业规划系统"
    APP_VERSION: str = "0.1.0"
    # 默认关闭：未显式配置即视为生产模式，默认密钥将阻止启动（见 _check_production_secrets）
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"  # DEBUG / INFO / WARNING / ERROR

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
    JOB_SOURCE_ENABLED: str = "jobui"    # 逗号分隔: jobui(职友集，中国真实岗位) / builtin(离线示例兜底，默认关闭)
    JOB_SYNC_INTERVAL_HOURS: float = 0.5  # 默认自动同步间隔（小时，0.5=30分钟；可在前端动态调整）
    JOB_SYNC_ON_STARTUP: bool = True      # 启动后立即同步一次

    @model_validator(mode="after")
    def _check_production_secrets(self) -> "Settings":
        """生产模式（DEBUG=false）禁止使用默认/弱密钥，直接拒绝启动；开发模式仅告警。"""
        uses_default_secret = self.JWT_SECRET == DEFAULT_JWT_SECRET or len(self.JWT_SECRET) < 32
        uses_default_aes = self.AES_KEY == DEFAULT_AES_KEY or len(self.AES_KEY) < 32
        if not self.DEBUG and (uses_default_secret or uses_default_aes):
            problems = []
            if uses_default_secret:
                problems.append(f"JWT_SECRET（当前 {len(self.JWT_SECRET)} 字符，需 ≥32 且非默认值）")
            if uses_default_aes:
                problems.append("AES_KEY（需 32 字节且非默认值）")
            raise ValueError(
                "生产模式（DEBUG=false）禁止使用默认密钥，拒绝启动。请设置强密钥：" + "、".join(problems)
            )
        if self.DEBUG and (uses_default_secret or uses_default_aes):
            warn(
                "开发模式正在使用默认密钥（JWT_SECRET/AES_KEY），生产部署前请务必替换。",
                stacklevel=2,
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

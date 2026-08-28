"""Embedding 适配层（设计 AD-04，工作包 A）。

原则：
- 向量检索是"可选增强"：未配置 EMBEDDING_* 或调用失败时，主流程自动降级为关键词检索；
- 任何异常都不阻断面试主流程，调用方负责捕获并回退；
- 支持 OpenAI 兼容的 /embeddings 接口（OpenAI / DeepSeek / Kimi / GLM / Qwen 等）。

用法：
    from app.rag.embedding import get_embedding_provider
    embedder = get_embedding_provider()   # None 表示不可用
    if embedder:
        vectors = embedder.embed(["问题文本"])
"""
import logging
from typing import Protocol

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):
    """Embedding 接口协议：embed(texts) -> list[list[float]]。"""

    name: str
    dimension: int | None

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class OpenAICompatEmbedding:
    """OpenAI 兼容 /embeddings 接口实现。

    失败时返回空列表（而非抛异常），由调用方决定降级策略。
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str = "BAAI/bge-m3",
        timeout: int = 30,
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self.name = model
        self.dimension: int | None = None

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(
                    f"{self._base_url}/embeddings",
                    json={"model": self._model, "input": texts},
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                items = sorted(data.get("data", []), key=lambda x: x.get("index", 0))
                vectors = [it["embedding"] for it in items if "embedding" in it]
                if vectors:
                    self.dimension = len(vectors[0])
                return vectors
        except Exception as exc:  # noqa: BLE001 - 必须兜底，绝不阻断主流程
            logger.warning("Embedding 调用失败（将降级为关键词检索）: %s", exc)
            return []


def get_embedding_provider() -> EmbeddingProvider | None:
    """根据全局配置创建 Embedding 实例；未配置或未启用返回 None。"""
    if not settings.EMBEDDING_ENABLED:
        return None
    if not settings.EMBEDDING_BASE_URL or not settings.EMBEDDING_API_KEY:
        logger.info("Embedding 未完整配置（缺 BASE_URL/API_KEY），向量检索关闭，使用关键词检索")
        return None
    return OpenAICompatEmbedding(
        api_key=settings.EMBEDDING_API_KEY,
        base_url=settings.EMBEDDING_BASE_URL,
        model=settings.EMBEDDING_MODEL or "BAAI/bge-m3",
        timeout=settings.EMBEDDING_TIMEOUT,
    )

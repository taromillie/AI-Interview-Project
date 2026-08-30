"""OpenAI 兼容接口实现（覆盖 DeepSeek/Kimi/GLM/Qwen 等）。"""
import asyncio
import logging
import time
from typing import AsyncIterator

from langchain_openai import ChatOpenAI

from app.llm.base import ChatMessage, LLMProvider

logger = logging.getLogger(__name__)

# 可重试的临时性错误：限流、网络抖动、超时、服务端 5xx
try:
    from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError

    RETRYABLE_EXCEPTIONS = (RateLimitError, APIConnectionError, APITimeoutError, InternalServerError)
except ImportError:  # 旧版 openai 无对应异常类
    RETRYABLE_EXCEPTIONS = ()

DEFAULT_MAX_RETRIES = 2  # 额外重试次数（最多 2 次）


class OpenAICompatProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str, model: str, max_retries: int = DEFAULT_MAX_RETRIES):
        self._client = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout=60,
            max_retries=0,  # 应用层自管重试，避免 SDK 内部静默重试放大延迟
        )
        self._model = model
        self._max_retries = max_retries

    @property
    def name(self) -> str:
        return self._model

    def _to_langchain(self, messages: list[ChatMessage]):
        return [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

    async def achat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            t0 = time.perf_counter()
            try:
                resp = await self._client.ainvoke(
                    self._to_langchain(messages),
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                logger.info(
                    "LLM achat model=%s msgs=%d dur=%.2fs",
                    self._model,
                    len(messages),
                    time.perf_counter() - t0,
                )
                return resp.content
            except RETRYABLE_EXCEPTIONS as exc:
                last_exc = exc
                if attempt >= self._max_retries:
                    raise
                wait = 0.5 * (2**attempt)
                logger.warning(
                    "LLM achat 可重试错误 model=%s 第%d/%d次 attempt err=%s，%.1fs 后重试",
                    self._model,
                    attempt + 1,
                    self._max_retries + 1,
                    exc,
                    wait,
                )
                await asyncio.sleep(wait)
            except Exception as exc:  # noqa: BLE001 - 非可重试错误（参数/鉴权/上下文超限等）直接抛
                logger.warning("LLM achat 失败 model=%s err=%s", self._model, exc)
                raise
        raise last_exc or RuntimeError("LLM achat 未知错误")

    def stream(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        from langchain_core.messages import AIMessageChunk

        stream = self._client.astream(
            self._to_langchain(messages),
            temperature=temperature,
            max_tokens=max_tokens,
        )

        async def _gen():
            t0 = time.perf_counter()
            try:
                async for chunk in stream:
                    if isinstance(chunk, AIMessageChunk):
                        yield chunk.content or ""
                    elif isinstance(chunk, dict):
                        yield chunk.get("content", "") or ""
                    else:
                        text = getattr(chunk, "content", "")
                        if text:
                            yield text
            finally:
                logger.info(
                    "LLM stream model=%s msgs=%d dur=%.2fs",
                    self._model,
                    len(messages),
                    time.perf_counter() - t0,
                )

        return _gen()

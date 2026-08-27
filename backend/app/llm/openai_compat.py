"""OpenAI 兼容接口实现（覆盖 DeepSeek/Kimi/GLM/Qwen 等）。"""
from typing import AsyncIterator

from langchain_openai import ChatOpenAI

from app.llm.base import ChatMessage, LLMProvider


class OpenAICompatProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str, model: str):
        self._client = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout=60,
        )
        self._model = model

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
        resp = await self._client.ainvoke(
            self._to_langchain(messages),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.content

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
            async for chunk in stream:
                if isinstance(chunk, AIMessageChunk):
                    yield chunk.content or ""
                elif isinstance(chunk, dict):
                    yield chunk.get("content", "") or ""
                else:
                    text = getattr(chunk, "content", "")
                    if text:
                        yield text

        return _gen()

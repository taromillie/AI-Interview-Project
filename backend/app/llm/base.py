"""LLM Provider 抽象接口：新增供应商只需实现此接口。"""
from abc import ABC, abstractmethod
from typing import AsyncIterator


class ChatMessage:
    def __init__(self, role: str, content: str):
        self.role = role  # system / user / assistant
        self.content = content


class LLMProvider(ABC):
    """统一的大模型调用接口。"""

    @abstractmethod
    async def achat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """非流式对话，返回完整文本。"""

    @abstractmethod
    def stream(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """流式对话，逐块产出文本片段。"""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

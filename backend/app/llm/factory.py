"""LLM Provider 工厂：按配置创建实例。"""
from app.core.config import settings
from app.llm.base import LLMProvider
from app.llm.openai_compat import OpenAICompatProvider

# 常见供应商默认地址
KNOWN_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "kimi": "https://api.moonshot.cn/v1",
    "glm": "https://open.bigmodel.cn/api/paas/v4",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
}

# 常见模型默认值
KNOWN_MODELS = {
    "deepseek": "deepseek-chat",
    "kimi": "moonshot-v1-8k",
    "glm": "glm-4-flash",
    "qwen": "qwen-plus",
}


def get_llm(
    provider_name: str,
    api_key: str,
    base_url: str | None = None,
    model: str | None = None,
) -> LLMProvider:
    """按供应商名称创建 LLM 实例。

    支持 deepseek / kimi / glm / qwen / openai 及任意 OpenAI 兼容地址。
    """
    name = (provider_name or "openai").lower().strip()
    if name not in KNOWN_BASE_URLS:
        # 自定义 Provider：必须显式提供 base_url 与 model
        if not base_url or not model:
            raise ValueError(f"未知 Provider {name}，需提供 base_url 与 model")
    resolved_url = base_url or KNOWN_BASE_URLS[name]
    resolved_model = model or KNOWN_MODELS.get(name, settings.DEFAULT_LLM_MODEL)
    return OpenAICompatProvider(
        api_key=api_key,
        base_url=resolved_url,
        model=resolved_model,
    )

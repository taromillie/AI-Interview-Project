"""LLM Provider 适配层：多供应商可插拔。"""
from app.llm.factory import get_llm

__all__ = ["get_llm"]

"""接口限流（FR-A-04）：按客户端 IP 限流，重点保护 LLM 消耗接口。"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

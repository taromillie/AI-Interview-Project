"""日志分级配置：统一控制台格式化输出，支持 LOG_LEVEL 环境变量（DEBUG/INFO/WARNING/ERROR）。"""
import logging
import sys

_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def setup_logging(level: str = "INFO") -> None:
    """初始化根日志器（幂等）：统一格式、控制台输出、压制访问日志噪音。"""
    level = (level or "INFO").upper()
    if level not in _LEVELS:
        level = "INFO"
    root = logging.getLogger()
    root.setLevel(level)
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)
    # 访问日志本身带状态码与耗时，降低其日志级别避免刷屏
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

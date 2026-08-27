"""统一异常体系与 FastAPI 异常处理器。"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """业务异常基类。

    code: 面向客户端的错误码（如 'RESUME_TOO_LARGE'）
    status: HTTP 状态码
    """

    def __init__(self, message: str, code: str = "APP_ERROR", status: int = 400):
        self.message = message
        self.code = code
        self.status = status
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status,
            content={"code": exc.code, "message": exc.message},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"code": "INTERNAL_ERROR", "message": "服务器内部错误"},
        )

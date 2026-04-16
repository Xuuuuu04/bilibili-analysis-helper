"""
================================================================================
FastAPI 应用工厂 (src/backend/http/app.py)
================================================================================

【架构位置】
这是 FastAPI 应用的核心工厂模块，位于 HTTP 层的顶部。
负责创建和配置 FastAPI 应用实例，是所有 HTTP 请求的入口。

【设计模式】
- 应用工厂模式（Application Factory Pattern）：
  将应用创建逻辑封装在函数中，而不是直接在模块级别创建

【主要功能】
1. 创建 FastAPI 应用实例
2. 注册全局异常处理器
3. 配置 CORS 中间件
4. 注册 API 路由
5. 挂载静态文件服务

【使用方式】
from src.backend.http.app import create_app
app = create_app()

【调用关系】
asgi.py (入口)
    └── create_app() (此函数)
            ├── 注册异常处理器
            ├── 添加 CORS 中间件
            ├── 注册 api_router
            └── 挂载静态文件

================================================================================
"""

import os
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.backend.http.api.router import api_router
from src.backend.http.core.errors import AppError
from src.backend.utils.http_client import close_http_session
from src.backend.utils.logger import get_logger
from src.backend.utils.request_context import set_request_id
from src.config import Config

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        yield
    finally:
        await close_http_session()


def create_app() -> FastAPI:
    """
    创建并配置 FastAPI 应用实例

    设计模式：应用工厂模式（Application Factory）

    为什么使用工厂模式？
    1. 延迟初始化：避免模块加载时就执行耗时操作
    2. 避免循环导入：其他模块可以在需要时才导入
    3. 测试友好：可以创建多个独立的应用实例进行测试

    Returns:
        FastAPI: 配置完成的应用实例
    """
    # 创建 FastAPI 实例
    app = FastAPI(title="Bilibili Analysis Helper", version="1.0.0", lifespan=lifespan)

    # 注册全局异常处理器 - 处理自定义业务异常
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code, content={"success": False, "error": exc.message}
        )

    # 注册全局异常处理器 - 处理请求验证异常
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, __: RequestValidationError):
        return JSONResponse(
            status_code=400, content={"success": False, "error": "请求参数验证失败"}
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception):
        logger.exception("Unhandled server error: %s", str(exc))
        return JSONResponse(status_code=500, content={"success": False, "error": "服务器内部错误"})

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        set_request_id(request_id)
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # 配置 CORS 中间件（如果启用）
    if Config.CORS_ENABLED:
        origins = [origin.strip() for origin in (Config.CORS_ORIGINS or "*").split(",")]
        allow_wildcard = origins == ["*"]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"] if allow_wildcard else origins,
            allow_credentials=not allow_wildcard,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # 注册 API 路由
    app.include_router(api_router)

    # 获取项目根目录（从当前文件向上 4 层）
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    static_dir = os.path.join(base_dir, "src", "frontend")
    assets_dir = os.path.join(base_dir, "assets")

    # 挂载静态文件服务
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")

    return app

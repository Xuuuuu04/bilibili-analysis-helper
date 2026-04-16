"""
================================================================================
设置管理路由 (src/backend/http/api/routes/settings.py)
================================================================================

【架构位置】
位于 HTTP 层的 API 路由子模块，定义应用设置相关的 HTTP 端点。

【设计模式】
- 路由模式 (Router Pattern): 使用 FastAPI 的 APIRouter 组织路由
- 依赖注入 (Dependency Injection): 使用 Depends 注入服务实例
- 配置模式: 集中管理应用配置

【主要功能】
1. 获取设置：
   - 端点: GET /api/settings
   - 功能: 获取当前应用配置
   - 安全: API Key 仅返回是否已设置，不返回实际值

2. 更新设置：
   - 端点: POST /api/settings
   - 功能: 更新应用配置
   - 持久化: 自动保存到 .env 文件

【可配置项】
- openai_api_base: API 服务地址
- openai_api_key: API 密钥
- model: 主分析模型
- qa_model: 问答模型
- deep_research_model: 深度研究模型
- exa_api_key: Exa 搜索 API 密钥
- dark_mode: 深色模式开关
- enable_research_thinking: 研究思考模式开关

【路由前缀】
/api

================================================================================
"""

from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from src.backend.http.api.schemas import SettingsUpdateRequest
from src.backend.http.dependencies import get_settings_service
from src.backend.http.usecases.settings_service import SettingsService

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/settings")
async def get_settings(settings_service: SettingsService = Depends(get_settings_service)):
    return await run_in_threadpool(settings_service.get_settings)


@router.post("/settings")
async def update_settings(
    payload: SettingsUpdateRequest,
    settings_service: SettingsService = Depends(get_settings_service),
):
    data = payload.model_dump(exclude_unset=True)
    return await run_in_threadpool(settings_service.update_settings, data)

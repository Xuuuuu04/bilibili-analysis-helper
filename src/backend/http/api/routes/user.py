"""
================================================================================
用户画像路由 (src/backend/http/api/routes/user.py)
================================================================================

【架构位置】
位于 HTTP 层的 API 路由子模块，定义用户画像相关的 HTTP 端点。

【设计模式】
- 路由模式 (Router Pattern): 使用 FastAPI 的 APIRouter 组织路由
- 依赖注入 (Dependency Injection): 使用 Depends 注入服务实例

【主要功能】
1. 获取用户画像：
   - 端点: POST /api/user/portrait
   - 功能: 分析并生成用户画像
   - 输入: 用户 UID 或用户名

【画像分析维度】
- 基本信息：粉丝数、获赞数、关注数等
- 内容风格：视频类型、时长分布、更新频率等
- 内容调性：搞笑/知识/生活/二次元等
- 受众画像：观众特征分析

【错误处理】
- 400: 缺少输入内容
- 404: 用户不存在或未找到

【路由前缀】
/api

================================================================================
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from src.backend.http.api.schemas import UserPortraitRequest
from src.backend.http.dependencies import get_user_service
from src.backend.http.usecases.user_service import UserService

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/user/portrait")
async def user_portrait(
    payload: UserPortraitRequest, user_service: UserService = Depends(get_user_service)
):
    if not payload.uid:
        return JSONResponse(status_code=400, content={"success": False, "error": "缺少输入内容"})
    return await run_in_threadpool(user_service.get_portrait, payload.uid)

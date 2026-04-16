"""
================================================================================
API 路由聚合模块 (src/backend/http/api/router.py)
================================================================================

【架构位置】
位于 HTTP 层的 API 子模块，负责聚合所有子路由。

【设计模式】
- 路由聚合模式：将所有子路由集中管理

【主要功能】
1. 创建主 API 路由器
2. 注册所有子路由模块
3. 统一路由前缀管理

【子路由列表】
- analyze.router: 视频分析路由
- bilibili.router: B站数据路由
- qa.router: 问答路由
- research.router: 深度研究路由
- settings.router: 设置路由
- user.router: 用户路由

【路由结构】
/api/analyze    → 视频分析
/api/qa         → 问答
/api/research   → 深度研究
/api/search     → 搜索
/api/user       → 用户画像
/api/settings   → 设置

================================================================================
"""

from fastapi import APIRouter

from src.backend.http.api.routes import analyze, bilibili, qa, research, settings, user

# 创建主 API 路由器
api_router = APIRouter()

# 注册所有子路由
api_router.include_router(analyze.router)
api_router.include_router(bilibili.router)
api_router.include_router(qa.router)
api_router.include_router(research.router)
api_router.include_router(settings.router)
api_router.include_router(user.router)

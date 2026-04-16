"""
================================================================================
依赖注入模块 (src/backend/http/dependencies.py)
================================================================================

【架构位置】
这是 FastAPI 依赖注入系统的核心模块，位于 HTTP 层。
负责提供所有路由处理器所需的服务实例。

【设计模式】
1. 依赖注入模式（Dependency Injection）：
   FastAPI 的 Depends 机制自动注入依赖

2. 单例模式（Singleton Pattern）：
   使用 @lru_cache 装饰器确保服务只创建一次

3. 工厂模式（Factory Pattern）：
   每个函数都是一个"工厂"，负责创建对应的服务实例

【主要功能】
1. 创建和管理所有服务实例
2. 处理服务之间的依赖关系
3. 确保核心服务是单例
4. 供 FastAPI 的 Depends() 使用

【使用方式】
在路由中使用 Depends() 自动注入服务：
    @router.post("/api/analyze")
    async def analyze(
        service: AnalyzeService = Depends(get_analyze_service)
    ):
        return await service.analyze(...)

【依赖关系图】
                    ┌─────────────────┐
                    │  dependencies  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ BilibiliService│    │  AIService    │    │ LoginService  │
│   (单例)       │    │   (单例)      │    │   (单例)      │
└───────┬───────┘    └───────┬───────┘    └───────────────┘
        │                    │
        └────────┬───────────┘
                 │
        ┌────────▼────────┐
        │  UseCase层服务   │
        │  (每次新建)      │
        └─────────────────┘
    - AnalyzeService
    - ResearchService
    - UserService

================================================================================
"""

from functools import lru_cache

from src.backend.http.core.errors import BadRequestError
from src.backend.http.usecases.analyze_service import AnalyzeService
from src.backend.http.usecases.research_service import ResearchService
from src.backend.http.usecases.settings_service import SettingsService
from src.backend.http.usecases.user_service import UserService
from src.backend.services.ai import AIService
from src.backend.services.bilibili import BilibiliService
from src.backend.services.bilibili.login_service import LoginService

# ========================================================================
# 基础服务提供者（单例模式）
# ========================================================================
# 这些服务是系统的核心，使用 @lru_cache 确保只创建一次
#
# 为什么使用单例？
# 1. BilibiliService 需要保持登录状态
# 2. AIService 需要复用 HTTP 连接池
# 3. 避免重复创建带来的性能开销


@lru_cache(maxsize=1)
def get_bilibili_service() -> BilibiliService:
    """获取 B站服务实例（单例）"""
    return BilibiliService()


@lru_cache(maxsize=1)
def get_ai_service() -> AIService:
    """获取 AI服务实例（单例）"""
    try:
        return AIService()
    except ValueError as exc:
        raise BadRequestError(str(exc)) from exc


@lru_cache(maxsize=1)
def get_login_service() -> LoginService:
    """获取登录服务实例（单例）"""
    return LoginService()


# ========================================================================
# 用例层服务提供者（工厂模式）
# ========================================================================
# 这些服务每次请求都会创建新实例
# 为什么不使用单例？用例服务通常是无状态的，创建成本低


def get_analyze_service() -> AnalyzeService:
    """获取分析服务实例（每次新建）"""
    return AnalyzeService(bilibili_service=get_bilibili_service(), ai_service=get_ai_service())


def get_research_service() -> ResearchService:
    """获取深度研究服务实例（每次新建）"""
    return ResearchService(ai_service=get_ai_service(), bilibili_service=get_bilibili_service())


@lru_cache(maxsize=1)
def get_settings_service() -> SettingsService:
    """获取设置服务实例（单例）"""
    return SettingsService()


def get_user_service() -> UserService:
    """获取用户服务实例（每次新建）"""
    return UserService(bilibili_service=get_bilibili_service(), ai_service=get_ai_service())

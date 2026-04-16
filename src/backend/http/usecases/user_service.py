"""
================================================================================
用户画像用例服务 (src/backend/http/usecases/user_service.py)
================================================================================

【架构位置】
位于 HTTP 层的用例子模块 (usecases/)，负责用户画像分析业务逻辑。

【设计模式】
- 用例模式 (Use Case Pattern): 封装用户画像分析流程
- 策略模式: 支持多种输入方式（UID 或 用户名）

【主要功能】
1. 获取用户画像：
   - 支持两种输入方式：
     * 直接输入 UID（数字）
     * 输入用户名（自动搜索获取 UID）
   - 获取用户基本信息
   - 获取用户近期作品
   - 调用 AI 生成用户画像分析

【输入输出】
输入: 用户 UID 或用户名
输出:
  - 用户基本信息
  - AI 生成的画像分析
  - 最近作品列表
  - Token 使用统计

【画像分析维度】
（由 AIService.generate_user_analysis 实现）
- 基本信息：粉丝数、获赞数等
- 内容风格：视频类型、时长分布等
- 内容调性：搞笑/知识/生活等
- 受众画像：观众特征分析

【错误处理】
- BadRequestError: 缺少输入内容
- NotFoundError: 用户不存在或未找到

================================================================================
"""

from typing import Optional

from src.backend.http.core.errors import BadRequestError, NotFoundError
from src.backend.services.ai import AIService
from src.backend.services.bilibili import BilibiliService, run_async


class UserService:
    def __init__(self, bilibili_service: BilibiliService, ai_service: AIService):
        self._bilibili = bilibili_service
        self._ai = ai_service

    def get_portrait(self, input_val: str):
        if not input_val:
            raise BadRequestError("缺少输入内容")

        target_uid: Optional[int] = None
        if str(input_val).isdigit():
            target_uid = int(input_val)
        else:
            search_res = run_async(self._bilibili.search_users(str(input_val), limit=1))
            if search_res.get("success") and search_res.get("data"):
                target_uid = search_res["data"][0]["mid"]
            else:
                raise NotFoundError(f'未找到名为 "{input_val}" 的用户')

        user_info_res = run_async(self._bilibili.get_user_info(target_uid))
        if not user_info_res.get("success"):
            raise NotFoundError(user_info_res.get("error", "用户不存在"))

        recent_videos_res = run_async(self._bilibili.get_user_recent_videos(target_uid))
        recent_videos = (
            recent_videos_res.get("data", []) if recent_videos_res.get("success") else []
        )

        portrait_data = self._ai.generate_user_analysis(user_info_res["data"], recent_videos)
        return {
            "success": True,
            "data": {
                "info": user_info_res["data"],
                "portrait": portrait_data["portrait"],
                "tokens_used": portrait_data["tokens_used"],
                "recent_videos": recent_videos,
            },
        }

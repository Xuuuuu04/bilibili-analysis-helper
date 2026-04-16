"""
================================================================================
设置管理用例服务 (src/backend/http/usecases/settings_service.py)
================================================================================

【架构位置】
位于 HTTP 层的用例子模块 (usecases/)，负责应用配置的管理和持久化。

【设计模式】
- 门面模式 (Facade Pattern): 为配置操作提供统一接口
- 写透模式 (Write-Through): 更新时同时写入文件和环境变量

【主要功能】
1. 获取设置：
   - 读取当前环境变量配置
   - 隐藏敏感信息（API Key 仅返回是否设置的状态）

2. 更新设置：
   - 持久化到 .env 文件
   - 更新运行时环境变量
   - 更新 Config 全局配置
   - 清除 AI 服务缓存以应用新配置

【配置项列表】
- OPENAI_API_BASE: API 服务地址
- OPENAI_API_KEY: API 密钥（敏感）
- model: 主分析模型
- QA_MODEL: 问答模型
- DEEP_RESEARCH_MODEL: 深度研究模型
- EXA_API_KEY: Exa 搜索 API 密钥（敏感）
- DARK_MODE: 深色模式开关
- ENABLE_RESEARCH_THINKING: 研究思考模式开关

【安全措施】
- API Key 不会完整返回给前端，仅返回是否已设置的布尔值
- 文件路径安全检查（防止目录遍历攻击）

================================================================================
"""

import os

from src.backend.utils.config_normalizer import normalize_openai_api_base
from src.backend.utils.env_store import upsert_env_values
from src.config import Config


class SettingsService:
    def get_settings(self) -> dict:
        openai_api_key = os.getenv("OPENAI_API_KEY") or ""
        exa_api_key = os.getenv("EXA_API_KEY") or ""
        return {
            "success": True,
            "data": {
                "openai_api_base": os.getenv("OPENAI_API_BASE"),
                "openai_api_key_set": bool(openai_api_key),
                "model": os.getenv("model"),
                "qa_model": os.getenv("QA_MODEL"),
                "deep_research_model": os.getenv(
                    "DEEP_RESEARCH_MODEL", "moonshotai/Kimi-K2-Thinking"
                ),
                "exa_api_key_set": bool(exa_api_key),
                "enable_research_thinking": os.getenv("ENABLE_RESEARCH_THINKING", "false").lower()
                == "true",
                "dark_mode": os.getenv("DARK_MODE", "false").lower() == "true",
            },
        }

    def update_settings(self, data: dict) -> dict:
        updates: dict[str, str] = {}

        if "openai_api_base" in data:
            base_url = normalize_openai_api_base(data.get("openai_api_base"))
            updates["OPENAI_API_BASE"] = base_url or ""
            os.environ["OPENAI_API_BASE"] = base_url or ""
            Config.OPENAI_API_BASE = base_url or ""

        if "openai_api_key" in data:
            api_key = (data.get("openai_api_key") or "").strip()
            if api_key:
                updates["OPENAI_API_KEY"] = api_key
                os.environ["OPENAI_API_KEY"] = api_key
                Config.OPENAI_API_KEY = api_key

        if "model" in data:
            model = data["model"] or ""
            updates["model"] = model
            os.environ["model"] = model
            Config.OPENAI_MODEL = model

        if "qa_model" in data:
            qa_model = data["qa_model"] or ""
            updates["QA_MODEL"] = qa_model
            os.environ["QA_MODEL"] = qa_model
            Config.QA_MODEL = qa_model

        if "deep_research_model" in data:
            deep_model = data["deep_research_model"] or ""
            updates["DEEP_RESEARCH_MODEL"] = deep_model
            os.environ["DEEP_RESEARCH_MODEL"] = deep_model
            Config.DEEP_RESEARCH_MODEL = deep_model

        if "exa_api_key" in data:
            exa_key = (data.get("exa_api_key") or "").strip()
            if exa_key:
                updates["EXA_API_KEY"] = exa_key
                os.environ["EXA_API_KEY"] = exa_key
                Config.EXA_API_KEY = exa_key

        if "dark_mode" in data:
            dark_mode = str(data["dark_mode"]).lower()
            updates["DARK_MODE"] = dark_mode
            os.environ["DARK_MODE"] = dark_mode

        if "enable_research_thinking" in data:
            enable_research_thinking = str(data["enable_research_thinking"]).lower()
            updates["ENABLE_RESEARCH_THINKING"] = enable_research_thinking
            os.environ["ENABLE_RESEARCH_THINKING"] = enable_research_thinking
            Config.ENABLE_RESEARCH_THINKING = enable_research_thinking == "true"

        if updates:
            upsert_env_values(updates)

        # 清除服务缓存，下次请求时用新配置重建实例
        from src.backend.http.dependencies import (
            get_ai_service,
            get_bilibili_service,
            get_login_service,
        )

        get_ai_service.cache_clear()
        get_bilibili_service.cache_clear()
        get_login_service.cache_clear()
        return {"success": True, "message": "设置已更新"}

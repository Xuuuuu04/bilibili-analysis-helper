"""
================================================================================
配置管理模块 (src/config.py)
================================================================================

【架构位置】
这是项目的全局配置中心，位于架构最顶层，被所有模块引用。
所有其他模块都通过导入 Config 类来获取配置参数。

【设计模式】
- 配置对象模式：使用类属性集中管理所有配置
- 环境变量模式：通过 .env 文件管理敏感信息
- 惰性初始化：只在需要时才进行配置处理

【主要功能】
1. 加载 .env 文件中的环境变量
2. 提供类型安全的配置访问
3. 处理配置默认值
4. 自动格式化 API Base URL

【使用方式】
from src.config import Config
api_key = Config.OPENAI_API_KEY
model = Config.OPENAI_MODEL

【配置分类】
- AI服务配置：OpenAI API Key、模型选择
- B站API配置：登录凭据
- 服务配置：监听地址、端口
- 缓存配置：Redis/内存缓存
- CORS配置：跨域设置
- 日志配置：日志级别、输出位置
================================================================================
"""

import os
import secrets
import logging

from dotenv import load_dotenv

from src.backend.utils.config_normalizer import normalize_openai_api_base

# 在模块加载时自动加载 .env 文件
# .env 文件应该位于项目根目录，包含所有敏感配置
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)


class Config:
    """
    应用配置类

    设计模式：配置对象模式 + 单例模式的变体
    - 所有配置都是类属性，全局共享
    - 无需实例化，直接通过类名访问
    - 配置在首次导入时初始化，之后保持不变

    使用示例：
        api_key = Config.OPENAI_API_KEY
        host = Config.HOST
    """

    # ========================================================================
    # AI 服务配置 (核心配置)
    # ========================================================================
    # OpenAI 兼容 API 的密钥，用于调用各种大模型
    # 支持：OpenAI 官方、SiliconCloud、Moonshot、通义千问等
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # API 基础 URL（代理地址）
    # 例如：https://api.siliconflow.cn/v1
    _api_base = os.getenv("OPENAI_API_BASE")
    OPENAI_API_BASE = normalize_openai_api_base(_api_base)

    # 主分析模型：用于视频分析、专栏分析等多模态任务
    # 建议：支持视觉的模型，如 Qwen2-VL、GPT-4V 等
    OPENAI_MODEL = os.getenv("model") or os.getenv("QA_MODEL", "Qwen/Qwen2.5-72B-Instruct")

    # 问答模型：用于智能问答、对话等文本任务
    # 建议：快速响应的文本模型，如 Qwen2.5-72B-Instruct
    QA_MODEL = os.getenv("QA_MODEL", "Qwen/Qwen2.5-72B-Instruct")

    # 深度研究模型：用于深度研究 Agent
    # 建议：支持长上下文、强推理能力的模型，如 Kimi-K2-Thinking
    DEEP_RESEARCH_MODEL = os.getenv("DEEP_RESEARCH_MODEL", "moonshotai/Kimi-K2-Thinking")

    # Exa 搜索 API 密钥（可选）
    # 用于智能小UP和深度研究的联网搜索功能
    EXA_API_KEY = os.getenv("EXA_API_KEY")

    # ========================================================================
    # 服务监听配置 (FastAPI / Uvicorn)
    # ========================================================================
    # 服务监听地址，0.0.0.0 表示监听所有网卡
    HOST = os.getenv("HOST", "0.0.0.0")

    # 服务监听端口
    PORT = int(os.getenv("PORT", 5001))

    # ========================================================================
    # B站 API 配置 (登录凭据)
    # ========================================================================
    # B站登录后获取的凭据，用于访问需要登录的接口
    # 这些凭据会自动保存到 .env 文件中
    BILIBILI_SESSDATA = os.getenv("BILIBILI_SESSDATA")
    BILIBILI_BILI_JCT = os.getenv("BILIBILI_BILI_JCT")
    BILIBILI_BUVID3 = os.getenv("BILIBILI_BUVID3")
    BILIBILI_DEDEUSERID = os.getenv("BILIBILI_DEDEUSERID")

    # ========================================================================
    # 小红书配置 (未来扩展)
    # ========================================================================
    XHS_COOKIE = os.getenv("XHS_COOKIE")

    # ========================================================================
    # 应用业务配置
    # ========================================================================
    # 字幕最大长度限制，防止内容过长导致 API 超限
    MAX_SUBTITLE_LENGTH = 50000

    # 请求超时时间（秒），防止请求卡死
    REQUEST_TIMEOUT = 300

    # 是否启用深度研究的思考模式
    # 某些模型（如 DeepSeek-V3、Kimi-K2）支持输出推理过程
    ENABLE_RESEARCH_THINKING = os.getenv("ENABLE_RESEARCH_THINKING", "false").lower() == "true"

    # ========================================================================
    # 环境配置
    # ========================================================================
    # 运行环境：development / production
    # 用于控制安全策略，如 JWT 密钥强制校验
    ENV = os.getenv("ENV", "development").lower()

    # ========================================================================
    # API 服务配置 (预留，暂未实现)
    # ========================================================================
    # 速率限制开关
    API_RATE_LIMIT_ENABLED = os.getenv("API_RATE_LIMIT_ENABLED", "True").lower() == "true"
    # 默认速率限制（请求数/窗口时间）
    API_RATE_LIMIT_DEFAULT = int(os.getenv("API_RATE_LIMIT_DEFAULT", 100))
    # 速率限制窗口时间（秒）
    API_RATE_LIMIT_WINDOW = int(os.getenv("API_RATE_LIMIT_WINDOW", 60))

    # ========================================================================
    # 认证配置 (预留，暂未实现)
    # ========================================================================
    API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")

    # JWT 密钥：生产环境必须设置环境变量
    _default_jwt_key = "default-secret-key-change-in-production"
    _jwt_key = os.getenv("JWT_SECRET_KEY")
    _env = os.getenv("ENV", "development").lower()
    if not _jwt_key:
        if _env in ("production", "prod"):
            raise ValueError("JWT_SECRET_KEY must be set in production")
        else:
            logger.warning("使用默认 JWT_SECRET_KEY，仅适合开发环境")
            _jwt_key = _default_jwt_key
    JWT_SECRET_KEY = _jwt_key

    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 24))

    # ========================================================================
    # 缓存配置
    # ========================================================================
    # 缓存开关
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "True").lower() == "true"
    # 缓存类型：memory（内存缓存）或 redis（Redis 缓存）
    CACHE_TYPE = os.getenv("CACHE_TYPE", "memory")
    # 缓存默认过期时间（秒）
    CACHE_DEFAULT_TTL = int(os.getenv("CACHE_DEFAULT_TTL", 3600))

    # Redis 配置（当 CACHE_TYPE=redis 时使用）
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

    # ========================================================================
    # CORS 配置 (跨域资源共享)
    # ========================================================================
    # CORS 开关
    CORS_ENABLED = os.getenv("CORS_ENABLED", "True").lower() == "true"
    # 允许的源，* 表示允许所有源
    # 多个源用逗号分隔，如：http://localhost:3000,https://example.com
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # ========================================================================
    # 日志配置
    # ========================================================================
    # 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    # 是否输出到文件
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "True").lower() == "true"
    # 日志文件目录
    LOG_DIR = os.getenv("LOG_DIR", "logs")

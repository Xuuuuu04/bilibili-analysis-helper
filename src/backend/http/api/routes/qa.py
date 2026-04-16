"""
================================================================================
通用问答路由 (src/backend/http/api/routes/qa.py)
================================================================================

【架构位置】
位于 HTTP 层的 API 路由子模块，定义智能问答相关的 HTTP 端点。

【设计模式】
- 路由模式 (Router Pattern): 使用 FastAPI 的 APIRouter 组织路由
- 依赖注入 (Dependency Injection): 使用 Depends 注入服务实例
- 流式响应模式: 使用 StreamingResponse + SSE 推送 AI 回复

【主要功能】
1. 智能问答流式接口：
   - 端点: POST /api/qa/stream
   - 功能: 基于上下文进行智能问答
   - 支持模式:
     * video: 视频相关问答
     * article: 专栏相关问答
     * user: 用户相关问答
     * research: 研究相关问答

【请求参数】
- question: 用户问题
- context: 上下文内容
- mode: 问答模式
- meta: 元数据（可选）
- history: 对话历史（可选）

【响应格式】
SSE 流式推送，包含以下类型：
- content: 回复内容片段
- stage: 处理阶段
- final: 最终结果
- error: 错误信息

【路由前缀】
/api

================================================================================
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.concurrency import iterate_in_threadpool

from src.backend.http.api.schemas import QAStreamRequest
from src.backend.http.api.utils import sse_data
from src.backend.http.dependencies import get_ai_service
from src.backend.services.ai import AIService

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/qa/stream")
async def qa_stream(payload: QAStreamRequest, ai_service: AIService = Depends(get_ai_service)):
    if not payload.question or not payload.context:
        return JSONResponse(status_code=400, content={"success": False, "error": "缺少必要参数"})

    def generate():
        try:
            for chunk in ai_service.context_qa_stream(
                mode=payload.mode,
                question=payload.question,
                context=payload.context,
                meta=payload.meta,
                history=payload.history,
            ):
                yield sse_data(chunk, ensure_ascii=False)
        except Exception as e:
            yield sse_data({"type": "error", "error": str(e)}, ensure_ascii=False)

    return StreamingResponse(iterate_in_threadpool(generate()), media_type="text/event-stream")

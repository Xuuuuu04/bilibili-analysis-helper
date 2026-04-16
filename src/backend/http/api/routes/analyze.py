"""
================================================================================
视频分析路由 (src/backend/http/api/routes/analyze.py)
================================================================================

【架构位置】
位于 HTTP 层的 API 路由子模块，定义视频分析相关的 HTTP 端点。

【设计模式】
- 路由模式 (Router Pattern): 使用 FastAPI 的 APIRouter 组织路由
- 依赖注入 (Dependency Injection): 使用 Depends 注入服务实例
- 流式响应模式: 使用 StreamingResponse + SSE 推送 AI 分析结果

【主要功能】
1. 视频对话分析：
   - 端点: POST /api/chat/stream
   - 功能: 基于视频内容进行智能问答对话
   - 响应: SSE 流式推送 AI 回复

2. 视频同步分析：
   - 端点: POST /api/analyze
   - 功能: 一次性分析视频并返回完整结果
   - 响应: JSON 完整响应

3. 视频流式分析：
   - 端点: POST /api/analyze/stream
   - 功能: 流式推送分析进度和结果
   - 响应: SSE 流式推送（包含进度提示）
   - 支持模式: video（视频）, article（专栏）

【技术要点】
- iterate_in_threadpool(): 将同步生成器转换为异步迭代器
- run_in_threadpool(): 在线程池中运行同步函数
- SSE 响应头: Cache-Control, Connection, CORS 配置

【路由前缀】
/api

================================================================================
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool

from src.backend.http.api.schemas import AnalyzeRequest, AnalyzeStreamRequest, ChatStreamRequest
from src.backend.http.api.utils import sse_data
from src.backend.http.dependencies import get_ai_service, get_analyze_service
from src.backend.http.usecases.analyze_service import AnalyzeService
from src.backend.services.ai import AIService

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/chat/stream")
async def chat_video_stream(
    payload: ChatStreamRequest, ai_service: AIService = Depends(get_ai_service)
):
    if not payload.question or not payload.context:
        return JSONResponse(status_code=400, content={"success": False, "error": "缺少必要参数"})

    def generate():
        try:
            for chunk in ai_service.chat_stream(
                payload.question, payload.context, payload.video_info, payload.history
            ):
                yield sse_data(chunk, ensure_ascii=False)
        except Exception as e:
            yield sse_data({"type": "error", "error": str(e)}, ensure_ascii=False)

    return StreamingResponse(iterate_in_threadpool(generate()), media_type="text/event-stream")


@router.post("/analyze")
async def analyze_video(
    payload: AnalyzeRequest,
    analyze_service: AnalyzeService = Depends(get_analyze_service),
):
    return await run_in_threadpool(analyze_service.analyze_video, payload.url)


@router.post("/analyze/stream")
async def analyze_video_stream(
    payload: AnalyzeStreamRequest,
    analyze_service: AnalyzeService = Depends(get_analyze_service),
):
    if not payload.url:
        return JSONResponse(
            status_code=400, content={"success": False, "error": "请提供B站视频或专栏链接"}
        )

    return StreamingResponse(
        iterate_in_threadpool(analyze_service.stream_analyze(payload.url, payload.mode)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )

"""
================================================================================
深度研究路由 (src/backend/http/api/routes/research.py)
================================================================================

【架构位置】
位于 HTTP 层的 API 路由子模块，定义深度研究相关的 HTTP 端点。

【设计模式】
- 路由模式 (Router Pattern): 使用 FastAPI 的 APIRouter 组织路由
- 依赖注入 (Dependency Injection): 使用 Depends 注入服务实例
- 流式响应模式: 使用 StreamingResponse + SSE 推送研究进度
- 文件服务模式: 使用 FileResponse 提供文件下载

【主要功能】
1. 启动深度研究：
   - 端点: POST /api/research
   - 功能: 根据课题进行深度研究
   - 响应: SSE 流式推送研究进度和结果

2. 查看研究历史：
   - 端点: GET /api/research/history
   - 功能: 列出所有历史研究报告

3. 下载研究报告：
   - 端点: GET /api/research/download/{file_id}/{format}
   - 功能: 下载指定格式的研究报告（md 或 pdf）

4. 查看报告内容：
   - 端点: GET /api/research/report/{filename}
   - 功能: 在线阅读报告内容

【文件路径安全】
- 检查路径遍历攻击（防止 ..、/、\）
- 文件格式白名单（仅允许 md、pdf）

【路由前缀】
/api

================================================================================
"""

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool

from src.backend.http.api.schemas import ResearchRequest
from src.backend.http.api.utils import sse_data
from src.backend.http.dependencies import get_research_service
from src.backend.http.usecases.research_service import ResearchService

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/research")
async def start_deep_research(
    payload: ResearchRequest,
    research_service: ResearchService = Depends(get_research_service),
):
    if not payload.topic:
        return JSONResponse(status_code=400, content={"success": False, "error": "请输入研究课题"})

    def generate():
        try:
            for chunk in research_service.stream(payload.topic):
                yield sse_data(chunk, ensure_ascii=False)
        except Exception as e:
            yield sse_data({"type": "error", "error": str(e)}, ensure_ascii=False)

    return StreamingResponse(iterate_in_threadpool(generate()), media_type="text/event-stream")


@router.get("/research/history")
async def list_research_history(research_service: ResearchService = Depends(get_research_service)):
    return await run_in_threadpool(research_service.list_history)


@router.get("/research/download/{file_id}/{format}")
async def download_research_report(
    file_id: str,
    format: str,
    research_service: ResearchService = Depends(get_research_service),
):
    filepath, filename = await run_in_threadpool(
        research_service.resolve_download_path, file_id, format
    )
    return FileResponse(path=filepath, filename=filename, media_type="application/octet-stream")


@router.get("/research/report/{filename}")
async def get_research_report(
    filename: str, research_service: ResearchService = Depends(get_research_service)
):
    return await run_in_threadpool(research_service.read_report, filename)

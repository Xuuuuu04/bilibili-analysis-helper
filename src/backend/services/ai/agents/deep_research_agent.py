"""
深度研究 Agent模块
提供全方位深度调研和报告撰写功能
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Generator

from openai import OpenAI

from src.backend.services.ai.ai_helpers import openai_chat_completions_stream, save_research_report
from src.backend.services.ai.prompts import (
    get_deep_research_system_prompt,
)
from src.backend.services.ai.toolkit import ToolRegistry
from src.backend.services.ai.toolkit.tools import (
    AnalyzeVideoTool,
    FinishResearchTool,
    GetHistoryPopularVideosTool,
    GetHotBuzzwordsTool,
    GetHotSearchKeywordsTool,
    GetHotVideosTool,
    GetRankVideosTool,
    GetSearchSuggestionsTool,
    GetUserDynamicsTool,
    GetUserRecentVideosTool,
    GetVideoSeriesTool,
    GetVideoTagsTool,
    GetWeeklyHotVideosTool,
    SearchUsersTool,
    SearchVideosTool,
    WebSearchTool,
)
from src.backend.utils.async_helpers import run_async
from src.backend.utils.bilibili_helpers import extract_bvid
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class DeepResearchAgent:
    """
    深度研究 Agent

    针对课题进行全方位深度调研，撰写专业研究报告
    """

    def __init__(
        self, client: OpenAI, model: str, vl_model: str = None, enable_thinking: bool = False
    ):
        """
        初始化深度研究 Agent

        Args:
            client: OpenAI客户端
            model: 使用的模型（深度研究）
            vl_model: 视觉语言模型（可选，用于视频帧分析）
            enable_thinking: 是否启用思考模式（用于支持thinking的混合态模型）
        """
        self.client = client
        self.model = model
        self.vl_model = vl_model or model  # 如果未指定，使用普通模型
        self.enable_thinking = enable_thinking

        # 初始化工具注册中心
        self._initialize_tools()

    def _initialize_tools(self):
        """初始化并注册所有工具"""
        # 清空之前的注册
        ToolRegistry.clear()

        # 注册核心工具
        tools = [
            SearchVideosTool(),
            AnalyzeVideoTool(),
            WebSearchTool(),
            SearchUsersTool(),
            GetUserRecentVideosTool(),
            GetHotVideosTool(),
            GetHotBuzzwordsTool(),
            GetWeeklyHotVideosTool(),
            GetHistoryPopularVideosTool(),
            GetRankVideosTool(),
            GetSearchSuggestionsTool(),
            GetHotSearchKeywordsTool(),
            GetVideoTagsTool(),
            GetVideoSeriesTool(),
            GetUserDynamicsTool(),
            FinishResearchTool(),
        ]

        for tool in tools:
            ToolRegistry.register(tool)
            # 设置AI客户端
            tool.set_ai_client(self.client, self.model)

        logger.info(f"[DeepResearchAgent] 已注册 {ToolRegistry.count()} 个工具")

    def stream_research(self, topic: str, bilibili_service) -> Generator[Dict, None, None]:
        """
        流式深度研究

        Args:
            topic: 研究课题
            bilibili_service: B站服务实例

        Yields:
            Dict: 包含状态、进度、内容等信息的字典
        """
        try:
            # 设置工具的bilibili_service
            ToolRegistry.set_services(bilibili_service=bilibili_service)

            run_id = uuid.uuid4().hex

            def _now_iso() -> str:
                return (
                    datetime.now(timezone.utc)
                    .isoformat(timespec="milliseconds")
                    .replace("+00:00", "Z")
                )

            def _emit(payload: Dict, tool_call_id=None) -> Dict:
                data = dict(payload or {})
                data.setdefault("run_id", run_id)
                data.setdefault("ts", _now_iso())
                data.setdefault("event_id", uuid.uuid4().hex)
                if tool_call_id and not data.get("tool_call_id"):
                    data["tool_call_id"] = tool_call_id
                return data

            think_state = {"in_think": False, "carry": ""}

            def _strip_think_blocks(text: str) -> str:
                if not text:
                    return ""
                open_tag = "<think>"
                close_tag = "</think>"
                s = (think_state["carry"] or "") + text
                think_state["carry"] = ""
                out: list[str] = []
                i = 0
                while i < len(s):
                    if not think_state["in_think"]:
                        if s.startswith(open_tag, i):
                            think_state["in_think"] = True
                            i += len(open_tag)
                            continue
                        remain = s[i:]
                        if len(remain) < len(open_tag) and open_tag.startswith(remain):
                            think_state["carry"] = remain
                            break
                        out.append(s[i])
                        i += 1
                        continue
                    if s.startswith(close_tag, i):
                        think_state["in_think"] = False
                        i += len(close_tag)
                        continue
                    remain = s[i:]
                    if len(remain) < len(close_tag) and close_tag.startswith(remain):
                        think_state["carry"] = remain
                        break
                    i += 1
                return "".join(out)

            system_prompt = get_deep_research_system_prompt(topic)

            tools = ToolRegistry.list_tools_schema()

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请针对以下课题开始深度研究：{topic}"},
            ]

            # 最大轮次限制，防止无限循环
            max_rounds = 100  # 深度研究提升至100轮
            round_count = 0

            for _ in range(max_rounds):
                round_count += 1
                yield _emit({"type": "round_start", "round": round_count})

                def maybe_compress_history():
                    total_chars = 0
                    for m in messages:
                        content = m.get("content")
                        if isinstance(content, str):
                            total_chars += len(content)
                    if total_chars < 200000:
                        return

                    tool_indices = [i for i, m in enumerate(messages) if m.get("role") == "tool"]
                    if len(tool_indices) <= 12:
                        return

                    keep_tool_indices = set(tool_indices[-10:])
                    summarize_tool_indices = [
                        i for i in tool_indices[:-10] if i not in keep_tool_indices
                    ]
                    if not summarize_tool_indices:
                        return

                    parts = []
                    for i in summarize_tool_indices:
                        m = messages[i]
                        name = m.get("name", "tool")
                        content = m.get("content", "")
                        if isinstance(content, str) and len(content) > 4000:
                            content = content[:3500] + "\n...\n" + content[-300:]
                        parts.append(f"[{name}]\n{content}")

                    user_text = "\n\n---\n\n".join(parts)
                    summarizer_messages = [
                        {
                            "role": "system",
                            "content": "你是一个严谨的研究助理。你将把历史工具输出压缩成可供后续推理使用的记忆，不要编造信息。",
                        },
                        {
                            "role": "user",
                            "content": "请将以下历史工具输出压缩成一段结构化记忆，要求：\n"
                            "1) 用小标题分段；2) 只保留关键事实、数据点与来源线索（视频标题/BV号/URL）；\n"
                            "3) 删除冗余细节；4) 不要加入新信息。\n\n"
                            f"{user_text}",
                        },
                    ]

                    try:
                        summary_stream = openai_chat_completions_stream(
                            self.client,
                            model=self.model,
                            messages=summarizer_messages,
                            stream=True,
                        )
                        summary_text = ""
                        for chunk in summary_stream:
                            if not chunk.choices:
                                continue
                            delta = chunk.choices[0].delta
                            if getattr(delta, "content", None):
                                summary_text += delta.content
                        if not summary_text.strip():
                            return

                        insert_at = min(keep_tool_indices)
                        new_messages = []
                        for idx, m in enumerate(messages):
                            if idx in summarize_tool_indices:
                                continue
                            if idx == insert_at:
                                new_messages.append(
                                    {
                                        "role": "system",
                                        "content": "【已压缩历史工具输出】\n"
                                        + summary_text.strip(),
                                    }
                                )
                            new_messages.append(m)
                        messages[:] = new_messages
                    except Exception:
                        return

                maybe_compress_history()

                # 构建API请求参数
                request_params = {
                    "model": self.model,
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto",
                    "stream": True,
                }

                # 如果启用思考模式，添加额外参数
                # 注意：只有部分模型（如DeepSeek-V3、Kimi-K2）支持这些参数
                if self.enable_thinking:
                    # 对于支持的模型，启用思考模式通常不需要额外参数
                    # 模型会自动返回 reasoning_content 字段
                    pass  # 某些模型可能需要额外的 max_tokens 等参数

                stream = openai_chat_completions_stream(self.client, **request_params)

                tool_calls = []
                full_content = ""

                # 处理流式响应
                for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta

                    if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                        yield _emit({"type": "thinking", "content": delta.reasoning_content})

                    if delta.content:
                        full_content += delta.content

                    if delta.tool_calls:
                        for tool_call in delta.tool_calls:
                            if len(tool_calls) <= tool_call.index:
                                tool_calls.append(
                                    {
                                        "id": tool_call.id,
                                        "type": "function",
                                        "function": {"name": "", "arguments": ""},
                                    }
                                )
                            if tool_call.id:
                                tool_calls[tool_call.index]["id"] = tool_call.id
                            if tool_call.function.name:
                                tool_calls[tool_call.index]["function"][
                                    "name"
                                ] += tool_call.function.name
                            if tool_call.function.arguments:
                                tool_calls[tool_call.index]["function"][
                                    "arguments"
                                ] += tool_call.function.arguments

                analyze_video_calls = [
                    tc for tc in tool_calls if tc.get("function", {}).get("name") == "analyze_video"
                ]

                batch_analyze_detected = len(analyze_video_calls) > 1
                if batch_analyze_detected:
                    logger.info(
                        f"[智能并行] 检测到 {len(analyze_video_calls)} 个 analyze_video 调用，将并行执行"
                    )

                # 如果没有工具调用，说明研究完成或模型直接给出了结论
                if not tool_calls:
                    # 核心修复：如果模型直接给出了内容但没有调用 finish 工具
                    if not any(
                        msg.get("role") == "tool"
                        and msg.get("name") == "finish_research_and_write_report"
                        for msg in messages
                    ):
                        if round_count < max_rounds:
                            messages.append({"role": "assistant", "content": full_content})
                            messages.append(
                                {
                                    "role": "user",
                                    "content": "研究尚未结束。请继续使用工具（如搜索相关视频、分析视频、搜索UP主或作品集）进行深入调研。只有当你认为资料完全充足时，请【务必调用】`finish_research_and_write_report` 工具来启动正式报告的撰写。不要直接在对话中结束。",
                                }
                            )
                            continue
                    messages.append({"role": "assistant", "content": full_content})
                    break

                # 处理工具调用
                messages.append(
                    {"role": "assistant", "content": full_content, "tool_calls": tool_calls}
                )

                # 如果检测到批量 analyze_video 调用，执行智能并行
                if batch_analyze_detected:
                    import asyncio
                    import concurrent.futures
                    import queue
                    import time

                    progress_queue: queue.Queue[dict] = queue.Queue()

                    analyze_call_meta = []
                    for tc in analyze_video_calls:
                        try:
                            args = json.loads(tc["function"]["arguments"])
                        except Exception:
                            args = {}
                        bvid = args.get("bvid")
                        analyze_call_meta.append({"tool_call": tc, "bvid": bvid})

                        yield _emit(
                            {
                                "type": "tool_start",
                                "tool": "analyze_video",
                                "args": {"bvid": bvid},
                            },
                            tc["id"],
                        )
                        yield _emit(
                            {
                                "type": "tool_progress",
                                "tool": "analyze_video",
                                "bvid": bvid,
                                "message": "已加入并行队列，正在启动分析任务...",
                            },
                            tc["id"],
                        )

                    max_workers = min(len(analyze_call_meta), 5)
                    results_by_tool_id: dict[str, dict] = {}

                    def analyze_single_video(
                        tool_call_id: str, bvid: str, progress_queue: "queue.Queue[dict]"
                    ) -> None:
                        try:
                            if bvid and ("bilibili.com" in bvid or "http" in bvid):
                                bvid = extract_bvid(bvid) or bvid
                            tool = ToolRegistry.get_tool("analyze_video")
                            if not tool:
                                progress_queue.put(
                                    {
                                        "kind": "done",
                                        "tool_call_id": tool_call_id,
                                        "bvid": bvid,
                                        "success": False,
                                        "error": "analyze_video 工具未注册",
                                        "tokens": 0,
                                    }
                                )
                                return

                            async def run_tool():
                                result_summary = ""
                                result_title = ""
                                async for item in tool.execute_stream(
                                    bvid=bvid, vl_model=self.vl_model
                                ):
                                    progress_queue.put(
                                        {
                                            "kind": "stream_item",
                                            "tool_call_id": tool_call_id,
                                            "bvid": bvid,
                                            "item": item,
                                        }
                                    )
                                    if item.get("type") == "tool_result":
                                        data = item.get("data") or {}
                                        result_title = data.get("title") or result_title
                                        result_summary = data.get("summary") or result_summary
                                    if item.get("type") == "error":
                                        break
                                return result_title, result_summary

                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                title, summary = new_loop.run_until_complete(run_tool())
                            finally:
                                new_loop.close()
                            progress_queue.put(
                                {
                                    "kind": "done",
                                    "tool_call_id": tool_call_id,
                                    "bvid": bvid,
                                    "title": title,
                                    "success": True if summary else False,
                                    "summary": summary,
                                    "tokens": len(summary) if summary else 0,
                                    "error": "" if summary else "分析未返回结果",
                                }
                            )
                        except Exception as e:
                            progress_queue.put(
                                {
                                    "kind": "done",
                                    "tool_call_id": tool_call_id,
                                    "bvid": bvid,
                                    "success": False,
                                    "error": str(e),
                                    "tokens": 0,
                                }
                            )

                    done_count = 0
                    last_activity = time.time()
                    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                        futures = [
                            executor.submit(
                                analyze_single_video,
                                m["tool_call"]["id"],
                                m["bvid"],
                                progress_queue,
                            )
                            for m in analyze_call_meta
                        ]

                        while done_count < len(analyze_call_meta):
                            try:
                                item = progress_queue.get(timeout=0.2)
                            except queue.Empty:
                                if all(f.done() for f in futures) and progress_queue.empty():
                                    if time.time() - last_activity > 2.0:
                                        break
                                continue

                            last_activity = time.time()
                            kind = item.get("kind")
                            if kind == "stream_item":
                                stream_item = item.get("item") or {}
                                if stream_item and stream_item.get("type") != "tool_result":
                                    stream_item.setdefault("tool", "analyze_video")
                                    yield _emit(stream_item, item.get("tool_call_id"))
                            elif kind == "done":
                                results_by_tool_id[item["tool_call_id"]] = item
                                done_count += 1

                                if item.get("success"):
                                    yield _emit(
                                        {
                                            "type": "tool_progress",
                                            "tool": "analyze_video",
                                            "bvid": item.get("bvid"),
                                            "title": item.get("title", ""),
                                            "message": f"✅ {item.get('title', item.get('bvid'))} 分析完成",
                                        },
                                        item.get("tool_call_id"),
                                    )
                                else:
                                    yield _emit(
                                        {
                                            "type": "tool_progress",
                                            "tool": "analyze_video",
                                            "bvid": item.get("bvid"),
                                            "message": f"❌ 分析失败: {item.get('error', '未知错误')}",
                                        },
                                        item.get("tool_call_id"),
                                    )

                    for m in analyze_call_meta:
                        tc_id = m["tool_call"]["id"]
                        if tc_id not in results_by_tool_id:
                            results_by_tool_id[tc_id] = {
                                "bvid": m["bvid"],
                                "success": False,
                                "error": "分析任务未返回结果",
                                "tokens": 0,
                            }

                    for tc in analyze_video_calls:
                        result_obj = results_by_tool_id.get(tc["id"]) or {
                            "bvid": None,
                            "success": False,
                            "error": "未知错误",
                            "tokens": 0,
                        }
                        if result_obj.get("success"):
                            summary = result_obj.get("summary", "")
                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tc["id"],
                                    "name": "analyze_video",
                                    "content": f"视频分析完成: {result_obj.get('title', result_obj.get('bvid'))}\n\n分析结果:\n{summary}",
                                }
                            )
                            yield _emit(
                                {
                                    "type": "tool_result",
                                    "tool": "analyze_video",
                                    "result": {
                                        "bvid": result_obj.get("bvid"),
                                        "title": result_obj.get("title"),
                                        "summary": summary,
                                    },
                                    "tokens": result_obj.get("tokens", 0),
                                },
                                tc["id"],
                            )
                        else:
                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tc["id"],
                                    "name": "analyze_video",
                                    "content": f"分析失败: {result_obj.get('error', '未知错误')}",
                                }
                            )

                    tool_calls = [
                        tc
                        for tc in tool_calls
                        if tc.get("function", {}).get("name") != "analyze_video"
                    ]

                # 正常的工具调用处理
                is_final_report_triggered = False
                for tool_call in tool_calls:
                    func_name = tool_call["function"]["name"]
                    try:
                        args = json.loads(tool_call["function"]["arguments"])
                    except Exception:
                        args = {}

                    yield _emit(
                        {"type": "tool_start", "tool": func_name, "args": args},
                        tool_call["id"],
                    )

                    try:
                        tool = ToolRegistry.get_tool(func_name)
                        if not tool:
                            result = f"工具不存在: {func_name}"
                            yield _emit({"type": "error", "error": result}, tool_call["id"])
                        elif hasattr(tool, "execute_stream"):
                            import queue
                            import threading

                            q: queue.Queue[dict] = queue.Queue()

                            def worker(_tool=tool, _args=args, _q=q, _func_name=func_name):
                                async def run():
                                    async for item in _tool.execute_stream(**_args):
                                        _q.put(item)
                                    _q.put({"type": "_done"})

                                try:
                                    run_async(run())
                                except Exception as e:
                                    _q.put({"type": "error", "tool": _func_name, "error": str(e)})
                                    _q.put({"type": "_done"})

                            t = threading.Thread(target=worker, daemon=True)
                            t.start()

                            tool_data = None
                            tool_error = ""
                            while True:
                                item = q.get()
                                if item.get("type") == "_done":
                                    break
                                if item.get("type") == "tool_result":
                                    tool_data = item.get("data")
                                    yield _emit(
                                        {
                                            "type": "tool_result",
                                            "tool": func_name,
                                            "result": tool_data,
                                        },
                                        tool_call["id"],
                                    )
                                elif item.get("type") == "tool_progress":
                                    item.setdefault("tool", func_name)
                                    yield _emit(item, tool_call["id"])
                                elif item.get("type") == "error":
                                    tool_error = item.get("error") or tool_error
                                    yield _emit(
                                        {"type": "error", "error": tool_error}, tool_call["id"]
                                    )
                                    break

                            if tool_data is not None:
                                if func_name == "analyze_video":
                                    summary = (tool_data or {}).get("summary") or ""
                                    title = (
                                        (tool_data or {}).get("title")
                                        or (tool_data or {}).get("bvid")
                                        or ""
                                    )
                                    result = f"视频分析完成: {title}\n\n分析结果:\n{summary}"
                                elif func_name == "finish_research_and_write_report":
                                    message = (tool_data or {}).get("message") or ""
                                    summary = (tool_data or {}).get("summary") or ""
                                    result = f"{message}\n\n研究摘要:\n{summary}".strip()
                                else:
                                    result = json.dumps(tool_data, ensure_ascii=False)
                            else:
                                result = f"执行工具出错: {tool_error or '未知错误'}"
                        else:
                            tool_result = run_async(ToolRegistry.execute_tool(func_name, **args))
                            if tool_result.get("type") == "error":
                                result = f"执行工具出错: {tool_result.get('error')}"
                                yield _emit(
                                    {"type": "error", "error": tool_result.get("error")},
                                    tool_call["id"],
                                )
                            else:
                                data = tool_result.get("data")
                                yield _emit(
                                    {"type": "tool_result", "tool": func_name, "result": data},
                                    tool_call["id"],
                                )
                                if func_name == "finish_research_and_write_report":
                                    message = (data or {}).get("message") or ""
                                    summary = (data or {}).get("summary") or ""
                                    result = f"{message}\n\n研究摘要:\n{summary}".strip()
                                else:
                                    result = json.dumps(data, ensure_ascii=False)
                    except Exception as e:
                        error_msg = str(e)
                        # 友好的401错误提示
                        if "401" in error_msg or "Invalid token" in error_msg:
                            error_msg = "API Key 校验失败（401 - Invalid token）。请在设置中检查您的 OpenAI API Key 和 API Base 是否正确。"
                        result = f"执行工具出错: {error_msg}"
                        yield _emit({"type": "error", "error": error_msg}, tool_call["id"])

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": func_name,
                            "content": result,
                        }
                    )

                    # 检查是否触发了最终报告
                    if func_name == "finish_research_and_write_report":
                        is_final_report_triggered = True

                # 如果触发了最终报告撰写，进入最后一段生成
                if is_final_report_triggered:
                    yield _emit({"type": "report_start"})

                    # 构建API请求参数
                    final_request_params = {
                        "model": self.model,
                        "messages": messages,
                        "stream": True,
                    }

                    # 如果启用思考模式，添加额外参数
                    if self.enable_thinking:
                        pass  # 模型会自动返回 reasoning_content

                    final_stream = openai_chat_completions_stream(
                        self.client, **final_request_params
                    )
                    final_report = ""
                    for chunk in final_stream:
                        if not chunk.choices:
                            continue
                        delta = chunk.choices[0].delta
                        if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                            yield _emit({"type": "thinking", "content": delta.reasoning_content})
                        if delta.content:
                            clean = _strip_think_blocks(delta.content)
                            if clean:
                                final_report += clean
                                if clean:
                                    yield _emit({"type": "content", "content": clean})

                    # 持久化报告
                    try:
                        save_research_report(topic, final_report)
                    except Exception as e:
                        logger.warning(f"保存报告失败: {e}")

                    break

            yield _emit({"type": "done"})

        except Exception as e:
            error_msg = str(e)
            # 友好的401错误提示
            if "401" in error_msg or "Invalid token" in error_msg:
                error_msg = "API Key 校验失败（401 - Invalid token）。请在设置中检查您的 OpenAI API Key 和 API Base 是否正确。"
            logger.error(f"深度研究失败: {error_msg}")
            import traceback

            traceback.print_exc()
            yield _emit({"type": "error", "error": error_msg})

"""
AI服务统一入口（重构版）
整合所有AI相关功能，提供向后兼容的接口
"""

import time
from typing import Callable, Dict, Generator, List, Optional

from openai import OpenAI

from src.backend.services.ai.agents.deep_research_agent import DeepResearchAgent
from src.backend.services.ai.ai_helpers import (
    extract_content_from_response,
    extract_tokens_from_response,
    parse_analysis_response,
)
from src.backend.services.ai.prompts import (
    get_article_analysis_prompt,
    get_chat_qa_system_prompt,
    get_context_qa_system_prompt,
    get_mindmap_prompt,
    get_summary_prompt,
    get_user_portrait_prompt,
    get_video_analysis_prompt,
)
from src.backend.utils.logger import get_logger
from src.backend.utils.retry import retry_sync
from src.config import Config

logger = get_logger(__name__)


class AIService:
    """
    AI服务统一入口类（向后兼容）

    整合所有AI相关功能：Agent、分析器、问答等
    """

    def __init__(self):
        """初始化AI服务"""
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 未配置，无法初始化 AIService")

        self.client = OpenAI(
            api_key=Config.OPENAI_API_KEY, base_url=Config.OPENAI_API_BASE, timeout=180.0
        )
        self.model = Config.OPENAI_MODEL or Config.QA_MODEL
        self.qa_model = Config.QA_MODEL
        self.research_model = Config.DEEP_RESEARCH_MODEL

        # 初始化 Agent（深度研究Agent需要视觉模型用于视频分析）
        self._deep_research_agent = DeepResearchAgent(
            self.client, self.research_model, vl_model=self.model
        )

    @staticmethod
    def _is_retryable_error(exc: Exception) -> bool:
        msg = str(exc).lower()
        return any(
            token in msg
            for token in ("timeout", "timed out", "connection", "429", "502", "503", "504")
        )

    def _create_completion(self, **kwargs):
        return retry_sync(
            lambda: self.client.chat.completions.create(**kwargs),
            retries=2,
            should_retry=self._is_retryable_error,
        )

    # ========== Agent 方法（保持向后兼容）==========

    def deep_research_stream(self, topic: str, bilibili_service) -> Generator[Dict, None, None]:
        """
        深度研究 Agent 逻辑

        Args:
            topic: 研究课题
            bilibili_service: B站服务实例

        Yields:
            Dict: 包含状态、进度、内容等信息的字典
        """
        return self._deep_research_agent.stream_research(topic, bilibili_service)

    # ========== 视频分析方法（保持向后兼容）==========

    def chat_stream(
        self, question: str, context: str, video_info: Dict, history: List[Dict] = None
    ) -> Generator[Dict, None, None]:
        """
        视频内容流式问答

        Args:
            question: 用户提问
            context: 视频分析结果上下文
            video_info: 视频基本信息
            history: 对话历史

        Yields:
            Dict: 包含内容的字典
        """
        try:
            if video_info is None:
                video_info = {}

            system_prompt = get_chat_qa_system_prompt(video_info, context)
            messages = [{"role": "system", "content": system_prompt}]

            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": question})

            stream = self._create_completion(
                model=self.qa_model, messages=messages, temperature=0.4, stream=True
            )

            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        yield {"type": "content", "content": delta.content}

            yield {"type": "done"}

        except Exception as e:
            logger.error(f"QA问答失败: {str(e)}")
            yield {"type": "error", "error": str(e)}

    def context_qa_stream(
        self,
        mode: str,
        question: str,
        context: str,
        meta: Optional[Dict] = None,
        history: Optional[List[Dict]] = None,
    ) -> Generator[Dict, None, None]:
        try:
            meta = meta or {}
            system_prompt = get_context_qa_system_prompt(mode, meta, context)
            messages = [{"role": "system", "content": system_prompt}]

            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": question})

            stream = self._create_completion(
                model=self.qa_model, messages=messages, temperature=0.4, stream=True
            )

            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        yield {"type": "content", "content": delta.content}

            yield {"type": "done"}

        except Exception as e:
            logger.error(f"上下文问答失败: {str(e)}")
            yield {"type": "error", "error": str(e)}

    def generate_full_analysis(
        self,
        video_info: Dict,
        content: str,
        video_frames: Optional[list] = None,
        retry_count: int = 0,
    ) -> Dict:
        """
        生成完整分析（包括总结和思维导图）

        Args:
            video_info: 视频信息
            content: 文本内容（字幕/弹幕）
            video_frames: 可选的视频帧（base64编码列表）
            retry_count: 重试次数

        Returns:
            {'success': bool, 'data': {分析结果}} 或 {'success': False, 'error': str}
        """
        try:
            logger.debug(f"开始生成分析 - 模型: {self.model}")
            logger.debug(f"API Base: {Config.OPENAI_API_BASE}")
            logger.debug(f"视频帧数量: {len(video_frames) if video_frames else 0}")

            danmaku_preview = None
            if content and "【弹幕内容（部分）】" in content:
                danmaku_preview = content
            prompt = get_video_analysis_prompt(
                video_info,
                content,
                has_video_frames=bool(video_frames),
                danmaku_content=danmaku_preview,
            )
            logger.debug(f"提示词长度: {len(prompt)}")

            # 构建消息内容
            user_content = [{"type": "text", "text": prompt}]

            if video_frames and len(video_frames) > 0:
                for idx, frame_base64 in enumerate(video_frames):
                    user_content.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{frame_base64}",
                                "detail": "low",
                            },
                        }
                    )
                    logger.debug(f"添加第 {idx+1} 帧到消息中")

            messages = [
                {
                    "role": "system",
                    "content": """你是一位资深的B站视频内容分析专家，擅长：
1. 深度内容解析 - 提取所有知识点、分析目的和含义
2. 结构化呈现 - 清晰的思维导图和层次结构
3. 互动数据分析 - 弹幕情感、热点、词云分析
4. 综合评价 - 多维度评分和学习建议

你能同时分析视频画面、文字内容和弹幕互动，提供全面、专业、易读的四大板块分析报告。
请严格按照要求的四大板块结构输出，内容详实、格式规范、逻辑清晰。""",
                },
                {"role": "user", "content": user_content},
            ]

            logger.debug("发送请求到API...")
            response = self._create_completion(
                model=self.model, messages=messages, temperature=0.2, max_tokens=8000, timeout=240
            )

            logger.debug(f"API响应类型: {type(response)}")

            # 处理响应
            analysis_text = extract_content_from_response(response)
            tokens_used = extract_tokens_from_response(response)
            parsed_content = parse_analysis_response(analysis_text)

            return {
                "success": True,
                "data": {
                    "full_analysis": analysis_text,
                    "parsed": parsed_content,
                    "tokens_used": tokens_used,
                },
            }
        except Exception as e:
            logger.error(f"生成完整分析失败: {str(e)}")
            logger.debug(f"错误类型: {type(e).__name__}")

            # 针对网络和超时错误的特殊处理
            if any(
                keyword in str(e).lower()
                for keyword in ["timeout", "connection", "network", "504", "502", "500"]
            ):
                if retry_count < 2:
                    logger.info(f"[重试] 检测到网络错误，正在进行第{retry_count + 1}次重试...")
                    logger.info(f"[重试] 错误详情: {str(e)}")

                    if video_frames and len(video_frames) > 4:
                        reduced_frames = video_frames[:4]
                        logger.warning(
                            f"[降级] 减少视频帧数量: {len(video_frames)} → {len(reduced_frames)}"
                        )
                        return self.generate_full_analysis(
                            video_info, content, reduced_frames, retry_count + 1
                        )
                    elif video_frames and retry_count == 0:
                        logger.warning("[降级] 放弃视频帧，仅使用文本分析")
                        return self.generate_full_analysis(
                            video_info, content, None, retry_count + 1
                        )

            import traceback

            traceback.print_exc()
            return {"success": False, "error": f"生成分析失败: {str(e)}"}

    def generate_full_analysis_stream(
        self,
        video_info: Dict,
        content: str,
        video_frames: Optional[list] = None,
        progress_callback: Optional[Callable] = None,
        _is_fallback: bool = False,
    ) -> Generator[Dict, None, None]:
        """
        流式生成完整分析

        Args:
            video_info: 视频信息
            content: 文本内容
            video_frames: 可选的视频帧
            progress_callback: 进度回调函数

        Yields:
            Dict: 包含状态、进度、内容块等信息的字典
        """
        try:
            # 降级调用时跳过初始 start 和 progress 事件，避免前端进度条重置
            if not _is_fallback:
                yield {
                    "type": "start",
                    "stage": "preparing",
                    "progress": 0,
                    "message": "准备生成分析...",
                    "tokens_used": 0,
                    "timestamp": time.time(),
                }

                if progress_callback:
                    progress_callback("preparing", 0, "准备生成分析...", 0)

            logger.debug(f"开始流式生成分析 - 模型: {self.model}")

            danmaku_preview = None
            if content and "【弹幕内容（部分）】" in content:
                danmaku_preview = content
            prompt = get_video_analysis_prompt(
                video_info,
                content,
                has_video_frames=bool(video_frames),
                danmaku_content=danmaku_preview,
            )

            if not _is_fallback:
                yield {
                    "type": "progress",
                    "stage": "building_prompt",
                    "progress": 10,
                    "message": "构建分析提示词...",
                    "tokens_used": 0,
                    "timestamp": time.time(),
                }

            # 构建消息内容
            user_content = [{"type": "text", "text": prompt}]

            if video_frames and len(video_frames) > 0:
                for idx, frame_base64 in enumerate(video_frames):
                    user_content.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{frame_base64}",
                                "detail": "low",
                            },
                        }
                    )
                    logger.debug(f"添加第 {idx+1} 帧到消息中")

            messages = [
                {
                    "role": "system",
                    "content": """你是一位资深的B站视频内容分析专家，擅长：
1. 深度内容解析 - 提取所有知识点、分析目的和含义
2. 结构化呈现 - 清晰的思维导图和层次结构
3. 互动数据分析 - 弹幕情感、热点、词云分析
4. 综合评价 - 多维度评分和学习建议

你能同时分析视频画面、文字内容和弹幕互动，提供全面、专业、易读的四大板块分析报告。
请严格按照要求的四大板块结构输出，内容详实、格式规范、逻辑清晰。""",
                },
                {"role": "user", "content": user_content},
            ]

            if not _is_fallback:
                yield {
                    "type": "progress",
                    "stage": "calling_api",
                    "progress": 20,
                    "message": "调用AI模型生成分析...",
                    "tokens_used": 0,
                    "timestamp": time.time(),
                }

                if progress_callback:
                    progress_callback("calling_api", 20, "调用AI模型生成分析...", 0)

            logger.debug("发送流式请求到API...")

            # 流式调用API
            stream = self._create_completion(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=8000,
                timeout=240,
                stream=True,
            )

            full_content = ""
            chunk_count = 0
            last_progress_update = time.time()

            if not _is_fallback:
                yield {
                    "type": "progress",
                    "stage": "streaming",
                    "progress": 30,
                    "message": "正在接收AI分析结果...",
                    "tokens_used": 0,
                    "timestamp": time.time(),
                }

            # 处理流式响应
            for chunk in stream:
                chunk_count += 1

                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        content_piece = delta.content
                        full_content += content_piece

                        # 每隔一定时间发送进度更新
                        current_time = time.time()
                        if current_time - last_progress_update > 0.5 or chunk_count % 10 == 0:
                            progress = min(30 + (chunk_count * 2), 90)

                            yield {
                                "type": "progress",
                                "stage": "streaming",
                                "progress": progress,
                                "message": "正在深度解析内容...",
                                "tokens_used": chunk_count * 10,
                                "content_length": len(full_content),
                                "timestamp": current_time,
                            }

                            if progress_callback:
                                progress_callback(
                                    "streaming", progress, "正在深度解析内容...", chunk_count * 10
                                )

                            last_progress_update = current_time

            # 最终处理
            yield {
                "type": "progress",
                "stage": "processing",
                "progress": 95,
                "message": "处理最终结果...",
                "tokens_used": chunk_count * 10,
                "timestamp": time.time(),
            }

            if progress_callback:
                progress_callback("processing", 95, "处理最终结果...", chunk_count * 10)

            # 解析最终结果
            parsed_content = parse_analysis_response(full_content)
            total_tokens = chunk_count * 15

            yield {
                "type": "complete",
                "stage": "completed",
                "progress": 100,
                "message": "分析完成！",
                "tokens_used": total_tokens,
                "content_length": len(full_content),
                "full_analysis": full_content,
                "parsed": parsed_content,
                "chunk_count": chunk_count,
                "timestamp": time.time(),
            }

            if progress_callback:
                progress_callback("completed", 100, "分析完成！", total_tokens)

            logger.debug(f"流式分析完成 - 总共 {chunk_count} 个chunk, 约 {total_tokens} tokens")

        except Exception as e:
            logger.error(f"流式生成分析失败: {str(e)}")
            logger.debug(f"错误类型: {type(e).__name__}")

            # 错误处理和降级策略
            if any(
                keyword in str(e).lower()
                for keyword in ["timeout", "connection", "network", "504", "502", "500"]
            ):
                yield {
                    "type": "error",
                    "stage": "retrying",
                    "progress": 0,
                    "message": f"网络错误，尝试降级处理... 错误: {str(e)}",
                    "error_type": "network",
                    "timestamp": time.time(),
                }

                # 降级到文本分析
                if video_frames:
                    yield {
                        "type": "progress",
                        "stage": "fallback",
                        "progress": 10,
                        "message": "降级到纯文本分析...",
                        "timestamp": time.time(),
                    }

                    # 递归调用，不使用视频帧，标记为降级调用
                    yield from self.generate_full_analysis_stream(
                        video_info, content, None, progress_callback, _is_fallback=True
                    )
                    return

            import traceback

            traceback.print_exc()

            yield {
                "type": "error",
                "stage": "failed",
                "progress": 0,
                "message": f"分析失败: {str(e)}",
                "error_type": type(e).__name__,
                "timestamp": time.time(),
            }

    # ========== 其他分析方法（保持向后兼容）==========

    def generate_summary(self, video_info: Dict, content: str) -> Dict:
        """生成视频总结"""
        try:
            prompt = get_summary_prompt(video_info, content)

            response = self._create_completion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的视频内容分析助手，擅长总结视频内容并提取关键信息。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=4000,
            )

            summary_text = extract_content_from_response(response)
            tokens_used = extract_tokens_from_response(response)

            return {"success": True, "data": {"summary": summary_text, "tokens_used": tokens_used}}
        except Exception as e:
            logger.error(f"生成总结失败: {str(e)}")
            import traceback

            traceback.print_exc()
            return {"success": False, "error": f"生成总结失败: {str(e)}"}

    def generate_mindmap(
        self, video_info: Dict, content: str, summary: Optional[str] = None
    ) -> Dict:
        """生成思维导图（Markdown格式）"""
        try:
            prompt = get_mindmap_prompt(video_info, content, summary)

            response = self._create_completion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的思维导图设计师，擅长将复杂内容结构化为清晰的思维导图。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )

            mindmap_text = extract_content_from_response(response)
            tokens_used = extract_tokens_from_response(response)

            return {"success": True, "data": {"mindmap": mindmap_text, "tokens_used": tokens_used}}
        except Exception as e:
            logger.error(f"生成思维导图失败: {str(e)}")
            import traceback

            traceback.print_exc()
            return {"success": False, "error": f"生成思维导图失败: {str(e)}"}

    def generate_article_analysis_stream(
        self, article_info: Dict, content: str
    ) -> Generator[Dict, None, None]:
        """专栏文章深度分析"""
        try:
            if article_info is None:
                article_info = {}
            prompt = get_article_analysis_prompt(article_info, content)

            messages = [
                {
                    "role": "system",
                    "content": "你是一位资深的B站专栏分析专家，擅长逻辑分析与深度总结。",
                },
                {"role": "user", "content": prompt},
            ]

            stream = self._create_completion(
                model=self.qa_model, messages=messages, temperature=0.3, stream=True
            )

            full_content = ""
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        full_content += delta.content
                        yield {"type": "content", "content": delta.content}

            # 解析文章内容
            sections = {
                "summary": full_content,
                "danmaku": "专栏文章暂无弹幕分析",
                "comments": "专栏文章暂无评论分析",
            }
            yield {"type": "final", "parsed": sections, "full_analysis": full_content}

        except Exception as e:
            yield {"type": "error", "error": str(e)}

    def generate_user_analysis(self, user_info: Dict, recent_videos: List[Dict]) -> Dict:
        """生成UP主深度画像（同步返回字典）"""
        try:
            videos_text = "\n".join(
                [
                    f"- {v.get('title', '未知标题')} (播放: {v.get('play', '未知')}, 时长: {v.get('length', '未知')})"
                    for v in recent_videos
                ]
            )
            prompt = get_user_portrait_prompt(user_info, videos_text)

            response = self._create_completion(
                model=self.qa_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=1000,
            )

            content = extract_content_from_response(response)
            tokens = extract_tokens_from_response(response)

            return {"portrait": content, "tokens_used": tokens}
        except Exception as e:
            return {"portrait": f"暂时无法生成UP主画像: {str(e)}", "tokens_used": 0}

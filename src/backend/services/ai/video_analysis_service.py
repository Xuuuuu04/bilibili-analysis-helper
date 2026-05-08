import time
import traceback
from typing import Callable, Dict, Generator, Optional

from openai import OpenAI

from src.backend.services.ai.ai_helpers import (
    extract_content_from_response,
    extract_tokens_from_response,
    parse_analysis_response,
)
from src.backend.services.ai.prompts import get_video_analysis_prompt
from src.backend.utils.logger import get_logger
from src.backend.utils.retry import retry_sync
from src.config import Config

logger = get_logger(__name__)


class VideoAnalysisService:
    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model

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

    def generate_full_analysis(
        self,
        video_info: Dict,
        content: str,
        video_frames: Optional[list] = None,
        retry_count: int = 0,
    ) -> Dict:
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
        try:
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

            for chunk in stream:
                chunk_count += 1

                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        content_piece = delta.content
                        full_content += content_piece

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

                if video_frames:
                    yield {
                        "type": "progress",
                        "stage": "fallback",
                        "progress": 10,
                        "message": "降级到纯文本分析...",
                        "timestamp": time.time(),
                    }

                    yield from self.generate_full_analysis_stream(
                        video_info, content, None, progress_callback, _is_fallback=True
                    )
                    return

            traceback.print_exc()

            yield {
                "type": "error",
                "stage": "failed",
                "progress": 0,
                "message": f"分析失败: {str(e)}",
                "error_type": type(e).__name__,
                "timestamp": time.time(),
            }

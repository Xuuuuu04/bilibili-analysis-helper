"""
================================================================================
视频分析用例服务 (src/backend/http/usecases/analyze_service.py)
================================================================================
"""

import asyncio
import json
from collections.abc import Iterator
from typing import Any, Literal

from src.backend.http.core.errors import BadRequestError
from src.backend.services.ai import AIService
from src.backend.services.bilibili import BilibiliService, run_async
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class AnalyzeService:
    def __init__(self, bilibili_service: BilibiliService, ai_service: AIService):
        self._bilibili = bilibili_service
        self._ai = ai_service

    @staticmethod
    def _sse(payload: dict[str, Any], ensure_ascii: bool = False) -> str:
        return f"data: {json.dumps(payload, ensure_ascii=ensure_ascii)}\n\n"

    @staticmethod
    def _safe_data(result: Any, default: Any) -> Any:
        if isinstance(result, dict) and result.get("success"):
            data = result.get("data")
            return default if data is None else data
        return default

    def _build_extra_context(
        self,
        stats_data: dict[str, Any],
        tags_data: dict[str, Any],
        series_data: dict[str, Any],
        related_data: list[dict[str, Any]],
        danmaku_texts: list[str],
        comments_data: list[dict[str, Any]],
    ) -> str:
        extra_context = ""
        if stats_data:
            extra_context += (
                "\n\n【统计】\n"
                f"- 播放: {stats_data.get('view')}\n"
                f"- 点赞: {stats_data.get('like')}\n"
                f"- 投币: {stats_data.get('coin')}\n"
                f"- 收藏: {stats_data.get('favorite')}\n"
                f"- 分享: {stats_data.get('share')}\n"
                f"- 弹幕数: {stats_data.get('danmaku')}\n"
                f"- 评论数: {stats_data.get('reply')}\n"
                f"- 在线: {stats_data.get('online')}"
            )
        if tags_data.get("tags"):
            tag_names = [t.get("tag_name") for t in tags_data.get("tags", []) if t.get("tag_name")]
            if tag_names:
                extra_context += "\n\n【标签】\n" + "、".join(tag_names[:30])
        if series_data.get("has_series"):
            extra_context += (
                "\n\n【所属合集】\n"
                f"- 合集: {series_data.get('series_title')}\n"
                f"- 总集数: {series_data.get('total_videos')}\n"
            )
            videos = series_data.get("videos") or []
            if videos:
                extra_context += "  - 同合集视频(部分): " + " | ".join(
                    [f"{v.get('index')}. {v.get('title')}" for v in videos[:10]]
                )
        if related_data:
            extra_context += "\n\n【相关推荐】\n" + "\n".join(
                [
                    f"- {r.get('title')}（UP: {r.get('author')} / 播放: {r.get('view')}）"
                    for r in related_data[:10]
                ]
            )
        if danmaku_texts:
            extra_context += "\n\n【实时弹幕（采样）】\n" + "\n".join(danmaku_texts[:400])
        if comments_data:
            comment_texts = [
                f"{c['username']} (赞:{c['like']}): {c['message']}" for c in comments_data[:200]
            ]
            extra_context += "\n\n【精彩评论（热门/高赞）】\n" + "\n".join(comment_texts)
        return extra_context

    def _collect_video_material(self, bvid: str, comment_target_count: int) -> dict[str, Any]:
        async def fetch_all():
            return await asyncio.gather(
                self._bilibili.get_video_subtitles(bvid),
                self._bilibili.get_video_danmaku(bvid, limit=1000),
                self._bilibili.get_video_comments(
                    bvid, max_pages=30, target_count=comment_target_count
                ),
                self._bilibili.get_video_stats(bvid),
                self._bilibili.get_video_tags(bvid),
                self._bilibili.get_video_series(bvid),
                self._bilibili.get_related_videos(bvid),
                return_exceptions=True,
            )

        (
            subtitle_result,
            danmaku_result,
            comments_result,
            stats_result,
            tags_result,
            series_result,
            related_result,
        ) = run_async(fetch_all())

        return {
            "subtitle_result": subtitle_result,
            "subtitle_data": self._safe_data(subtitle_result, {}),
            "danmaku_texts": self._safe_data(danmaku_result, {}).get("danmakus", []),
            "comments_data": self._safe_data(comments_result, {}).get("comments", []),
            "stats_data": self._safe_data(stats_result, {}),
            "tags_data": self._safe_data(tags_result, {}),
            "series_data": self._safe_data(series_result, {}),
            "related_data": self._safe_data(related_result, []),
        }

    def _build_content(self, material: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        subtitle_result = material["subtitle_result"]
        subtitle_data = material["subtitle_data"]
        if not (
            isinstance(subtitle_result, dict)
            and subtitle_result.get("success")
            and subtitle_data.get("has_subtitle")
        ):
            return False, "", {}

        content = subtitle_data.get("full_text", "")
        content += self._build_extra_context(
            stats_data=material["stats_data"],
            tags_data=material["tags_data"],
            series_data=material["series_data"],
            related_data=material["related_data"],
            danmaku_texts=material["danmaku_texts"],
            comments_data=material["comments_data"],
        )
        return True, content, subtitle_data

    def analyze_video(self, url: str) -> dict[str, Any]:
        if not url:
            raise BadRequestError("请提供B站视频链接")

        bvid = BilibiliService.extract_bvid(url)
        if not bvid:
            raise BadRequestError("无效的B站视频链接")

        video_info_result = run_async(self._bilibili.get_video_info(bvid))
        if not video_info_result.get("success"):
            raise BadRequestError(video_info_result.get("error", "获取视频信息失败"))
        video_info = video_info_result["data"]

        material = self._collect_video_material(bvid, comment_target_count=300)
        ok, content, subtitle_data = self._build_content(material)
        if not ok:
            raise BadRequestError("该视频未获取到字幕、AI 总结或简介，无法进行分析。")
        if not content or len(content) < 50:
            raise BadRequestError("字幕内容过短，无法进行有效分析")

        frames_result = run_async(self._bilibili.extract_video_frames(bvid))
        video_frames = frames_result["data"]["frames"] if frames_result.get("success") else None
        if not video_frames:
            raise BadRequestError("未能提取关键帧。当前分析模式要求必须有关键帧。")

        analysis_result = self._ai.generate_full_analysis(video_info, content, video_frames)
        if not analysis_result.get("success"):
            raise BadRequestError(analysis_result.get("error", "AI 分析失败"))

        return {
            "success": True,
            "data": {
                "video_info": video_info,
                "stats": material["stats_data"],
                "has_subtitle": True,
                "subtitle_is_ai": bool(subtitle_data.get("is_ai")),
                "subtitle_selected_track": subtitle_data.get("selected_track"),
                "subtitle_tracks": subtitle_data.get("tracks"),
                "has_video_frames": bool(video_frames),
                "frame_count": len(video_frames),
                "content": content,
                "content_length": len(content),
                "danmaku_count": len(material["danmaku_texts"]),
                "comment_count": len(material["comments_data"]),
                "danmaku_preview": material["danmaku_texts"][:20],
                "comments_preview": material["comments_data"][:10],
                "analysis": analysis_result["data"]["full_analysis"],
                "parsed": analysis_result["data"]["parsed"],
                "tokens_used": analysis_result["data"]["tokens_used"],
            },
        }

    def stream_analyze(self, url: str, mode: Literal["video", "article"]) -> Iterator[str]:
        if not url:
            yield self._sse(
                {"type": "error", "error": "请提供B站视频或专栏链接"}, ensure_ascii=False
            )
            return

        bvid = BilibiliService.extract_bvid(url)
        article_meta = BilibiliService.extract_article_id(url)

        try:
            if not bvid and not article_meta:
                yield self._sse(
                    {
                        "type": "stage",
                        "stage": "searching",
                        "message": "正在为您搜索相关内容...",
                        "progress": 5,
                    }
                )

                if mode == "article":
                    search_res = run_async(self._bilibili.search_articles(url, limit=1))
                    if search_res.get("success") and search_res.get("data"):
                        article_meta = {"type": "cv", "id": search_res["data"][0]["cvid"]}
                        title = search_res["data"][0].get("title", "")
                        yield self._sse(
                            {
                                "type": "stage",
                                "stage": "search_complete",
                                "message": f"为您找到专栏: {title}",
                                "progress": 10,
                            },
                            ensure_ascii=False,
                        )
                    else:
                        yield self._sse({"type": "error", "error": "未找到相关专栏内容"})
                        return
                else:
                    search_res = run_async(self._bilibili.search_videos(url, limit=1))
                    if search_res.get("success") and search_res.get("data"):
                        bvid = search_res["data"][0]["bvid"]
                        title = search_res["data"][0].get("title", "")
                        yield self._sse(
                            {
                                "type": "stage",
                                "stage": "search_complete",
                                "message": f"为您找到视频: {title}",
                                "progress": 10,
                            },
                            ensure_ascii=False,
                        )
                    else:
                        yield self._sse({"type": "error", "error": "未找到相关视频"})
                        return

            if article_meta:
                a_type = article_meta["type"]
                a_id = article_meta["id"]

                yield self._sse(
                    {
                        "type": "stage",
                        "stage": "fetching_info",
                        "message": f"获取{a_type}信息...",
                        "progress": 10,
                    }
                )
                res = (
                    run_async(self._bilibili.get_article_content(a_id))
                    if a_type == "cv"
                    else run_async(self._bilibili.get_opus_content(a_id))
                )
                if not res.get("success"):
                    yield self._sse({"type": "error", "error": res.get("error", "未知错误")})
                    return

                info = res["data"]
                title = info.get("title", "")
                yield self._sse(
                    {
                        "type": "stage",
                        "stage": "info_complete",
                        "message": f"已获取内容: {title}",
                        "progress": 20,
                        "info": info,
                    },
                    ensure_ascii=False,
                )
                yield self._sse(
                    {
                        "type": "stage",
                        "stage": "starting_analysis",
                        "message": "正在深度解析内容...",
                        "progress": 40,
                    }
                )

                for chunk in self._ai.generate_article_analysis_stream(
                    res["data"], res["data"]["content"]
                ):
                    yield self._sse(chunk, ensure_ascii=False)

                yield self._sse(
                    {
                        "type": "final",
                        "stage": "completed",
                        "message": "专栏分析完成！",
                        "progress": 100,
                        "content": info.get("content", ""),
                        "info": info,
                    },
                    ensure_ascii=False,
                )
                return

            yield self._sse(
                {
                    "type": "stage",
                    "stage": "fetching_info",
                    "message": "获取视频信息...",
                    "progress": 5,
                }
            )
            video_info_result = run_async(self._bilibili.get_video_info(bvid))
            if not video_info_result.get("success"):
                yield self._sse(
                    {"type": "error", "error": video_info_result.get("error", "获取视频信息失败")}
                )
                return

            video_info = video_info_result["data"]
            video_title = video_info.get("title", "")
            yield self._sse(
                {
                    "type": "stage",
                    "stage": "info_complete",
                    "message": f"已获取视频信息: {video_title}",
                    "progress": 15,
                },
                ensure_ascii=False,
            )
            yield self._sse(
                {
                    "type": "stage",
                    "stage": "fetching_content",
                    "message": "获取字幕和弹幕...",
                    "progress": 20,
                }
            )

            material = self._collect_video_material(bvid, comment_target_count=500)
            ok, content, subtitle_data = self._build_content(material)
            if not ok:
                yield self._sse(
                    {"type": "error", "error": "该视频没有字幕、AI 总结或简介，无法进行分析。"},
                    ensure_ascii=False,
                )
                return

            text_source = subtitle_data.get("text_source", "未知")
            yield self._sse(
                {
                    "type": "stage",
                    "stage": "content_ready",
                    "message": f"使用{text_source}内容（{len(content)}字）",
                    "progress": 35,
                    "content": content,
                    "has_subtitle": True,
                    "text_source": text_source,
                    "subtitle_is_ai": bool(subtitle_data.get("is_ai")),
                    "subtitle_selected_track": subtitle_data.get("selected_track"),
                },
                ensure_ascii=False,
            )

            if len(content) < 50:
                yield self._sse(
                    {"type": "error", "error": "无法获取视频内容（无字幕且无有效弹幕）"}
                )
                return

            yield self._sse(
                {
                    "type": "stage",
                    "stage": "extracting_frames",
                    "message": "提取视频关键帧...",
                    "progress": 40,
                }
            )
            frames_result = run_async(self._bilibili.extract_video_frames(bvid))
            if not frames_result.get("success"):
                yield self._sse(
                    {"type": "error", "error": "未能提取关键帧。当前分析模式要求必须有关键帧。"},
                    ensure_ascii=False,
                )
                return

            video_frames = frames_result["data"]["frames"]
            frame_count = len(video_frames)
            yield self._sse(
                {
                    "type": "stage",
                    "stage": "frames_ready",
                    "message": f"成功提取 {frame_count} 帧画面",
                    "progress": 50,
                    "has_frames": True,
                    "frame_count": frame_count,
                }
            )
            yield self._sse(
                {
                    "type": "stage",
                    "stage": "starting_analysis",
                    "message": "开始AI智能分析...",
                    "progress": 55,
                }
            )

            for chunk in self._ai.generate_full_analysis_stream(video_info, content, video_frames):
                yield self._sse(chunk, ensure_ascii=False)

            top_comments = sorted(
                material["comments_data"], key=lambda item: item.get("like", 0), reverse=True
            )[:8]
            login_info = " (已登录)" if self._bilibili.credential else " (未登录)"
            yield self._sse(
                {
                    "type": "final",
                    "stage": "completed",
                    "message": f"分析完成！{login_info}",
                    "progress": 100,
                    "content": content,
                    "top_comments": top_comments,
                    "danmaku_preview": material["danmaku_texts"][:200],
                    "frame_count": frame_count,
                    "comments_count": len(material["comments_data"]),
                    "danmaku_count": len(material["danmaku_texts"]),
                },
                ensure_ascii=False,
            )
        except Exception as e:
            logger.error("流式分析异常: %s", str(e))
            yield self._sse(
                {"type": "error", "error": f"分析过程中发生错误: {str(e)}"},
                ensure_ascii=False,
            )

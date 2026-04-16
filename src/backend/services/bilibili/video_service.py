"""
B站视频服务模块
提供视频信息、字幕、弹幕、评论、统计等功能
"""

import base64
from typing import Dict, Optional

import aiohttp
import cv2
import numpy as np
from bilibili_api import comment, video

from src.backend.utils.bilibili_helpers import (
    calculate_optimal_frame_params,
    format_duration,
    smart_sample_danmaku,
)
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class VideoService:
    """
    B站视频服务类

    提供视频相关的所有功能：信息获取、字幕、弹幕、评论、统计、相关视频、热门推荐、视频帧提取
    """

    def __init__(self, credential=None):
        """
        初始化视频服务

        Args:
            credential: B站登录凭据（可选）
        """
        self.credential = credential

    async def get_info(self, bvid: str) -> Dict:
        """
        获取视频基本信息

        Args:
            bvid: 视频BVID

        Returns:
            {'success': bool, 'data': {视频信息}} 或 {'success': False, 'error': str}
        """
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            duration = info.get("duration", 0)

            return {
                "success": True,
                "data": {
                    "bvid": info.get("bvid"),
                    "title": info.get("title"),
                    "desc": info.get("desc"),
                    "duration": duration,
                    "duration_str": format_duration(duration),
                    "author": info.get("owner", {}).get("name"),
                    "view": info.get("stat", {}).get("view"),
                    "like": info.get("stat", {}).get("like"),
                    "cover": info.get("pic"),
                    "pubdate": info.get("pubdate"),
                    "aid": info.get("aid"),
                },
            }
        except Exception as e:
            return {"success": False, "error": f"获取视频信息失败: {str(e)}"}

    async def get_subtitles(self, bvid: str, prefer_ai: bool = True) -> Dict:
        """
        获取视频字幕

        Args:
            bvid: 视频BVID

        Returns:
            {'success': bool, 'data': {字幕信息}} 或 {'success': False, 'error': str}
        """
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            cid = info.get("cid")
            if not cid:
                return {"success": True, "data": {"has_subtitle": False, "subtitles": []}}

            subtitle_info = await v.get_subtitle(cid=cid)
            subtitles_list = subtitle_info.get("subtitles", []) if subtitle_info else []

            tracks = []
            for s in subtitles_list:
                lan = (s.get("lan") or "").strip()
                lan_doc = (s.get("lan_doc") or "").strip()
                lan_doc_lower = lan_doc.lower()
                is_ai = any(
                    x in lan_doc_lower for x in ["ai", "auto", "自动", "机器", "智能", "自动生成"]
                )
                subtitle_url = s.get("subtitle_url") or ""
                if subtitle_url.startswith("//"):
                    subtitle_url = "https:" + subtitle_url
                elif subtitle_url.startswith("/"):
                    subtitle_url = "https://aisubtitle.hdslb.com" + subtitle_url
                elif subtitle_url and not subtitle_url.startswith(("http://", "https://")):
                    subtitle_url = "https://" + subtitle_url
                tracks.append(
                    {
                        "lan": lan,
                        "lan_doc": lan_doc,
                        "is_ai": is_ai,
                        "subtitle_url": subtitle_url,
                    }
                )

            selected_track = None
            subtitle_text = []
            fetch_errors = []

            if tracks:

                def is_zh(t: Dict) -> bool:
                    lan = (t.get("lan") or "").lower()
                    lan_doc = (t.get("lan_doc") or "").lower()
                    return ("zh" in lan) or ("中文" in lan_doc) or ("chinese" in lan_doc)

                ai_zh = [t for t in tracks if is_zh(t) and t.get("is_ai")]
                human_zh = [t for t in tracks if is_zh(t) and not t.get("is_ai")]
                other_ai = [t for t in tracks if (not is_zh(t)) and t.get("is_ai")]
                other = [t for t in tracks if not t.get("is_ai")]

                candidates = []
                if prefer_ai:
                    candidates.extend(ai_zh)
                    candidates.extend(other_ai)
                    candidates.extend(human_zh)
                    candidates.extend(other)
                else:
                    candidates.extend(human_zh)
                    candidates.extend(ai_zh)
                    candidates.extend(other)
                    candidates.extend(other_ai)

                for t in candidates:
                    subtitle_url = t.get("subtitle_url") or ""
                    if not subtitle_url:
                        continue
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(subtitle_url) as resp:
                                subtitle_data = await resp.json()
                        body = (
                            subtitle_data.get("body", []) if isinstance(subtitle_data, dict) else []
                        )
                        subtitle_text = [
                            item.get("content", "").strip()
                            for item in body
                            if isinstance(item, dict) and item.get("content", "").strip()
                        ]
                        if subtitle_text:
                            selected_track = t
                            break
                    except Exception as e:
                        fetch_errors.append(f"{t.get('lan_doc') or t.get('lan')}: {str(e)}")

            if not subtitle_text:
                # 备选方案 1: 尝试获取 AI 总结 (AI Conclusion) 作为文本来源
                try:
                    res = await v.get_ai_conclusion(cid=cid)
                    if res and "model_result" in res:
                        mr = res["model_result"]
                        summary = mr.get("summary") or ""
                        outline = mr.get("outline") or []

                        fallback_lines = []
                        if summary:
                            fallback_lines.append(f"[AI 总结]\n{summary}")

                        if outline:
                            fallback_lines.append("[AI 视频大纲]")
                            for item in outline:
                                title = item.get("title", "")
                                part_desc = item.get("part_outline", "")
                                timestamp = item.get("timestamp", 0)
                                time_str = format_duration(timestamp)
                                fallback_lines.append(f"{time_str} {title}")
                                if part_desc:
                                    fallback_lines.append(f"  - {part_desc}")

                        if fallback_lines:
                            return {
                                "success": True,
                                "data": {
                                    "has_subtitle": True,
                                    "subtitles": fallback_lines,
                                    "full_text": "\n".join(fallback_lines),
                                    "language": "中文 (AI 总结)",
                                    "is_ai": True,
                                    "text_source": "AI 总结",
                                    "tracks": tracks,
                                },
                            }
                except Exception as e:
                    logger.warning(f"尝试获取 AI 总结失败: {e}")

                # 备选方案 2: 最终兜底使用视频简介
                desc = info.get("desc") or ""
                if desc:
                    return {
                        "success": True,
                        "data": {
                            "has_subtitle": True,
                            "subtitles": [desc],
                            "full_text": f"[视频简介]\n{desc}",
                            "language": "中文 (视频简介)",
                            "is_ai": False,
                            "text_source": "视频简介",
                            "tracks": tracks,
                        },
                    }

                return {
                    "success": True,
                    "data": {
                        "has_subtitle": False,
                        "subtitles": [],
                        "tracks": tracks,
                        "error": "未能成功拉取任何字幕、AI 总结或简介",
                        "fetch_errors": fetch_errors[:5],
                    },
                }

            return {
                "success": True,
                "data": {
                    "has_subtitle": True,
                    "subtitles": subtitle_text,
                    "full_text": "\n".join(subtitle_text),
                    "language": (selected_track or {}).get("lan_doc") or "未知",
                    "is_ai": bool((selected_track or {}).get("is_ai")),
                    "text_source": "字幕",
                    "selected_track": selected_track,
                    "tracks": tracks,
                },
            }
        except Exception as e:
            return {"success": False, "error": f"获取字幕失败: {str(e)}"}

    async def get_danmaku(self, bvid: str, limit: int = 1000) -> Dict:
        """
        获取视频弹幕

        Args:
            bvid: 视频BVID
            limit: 获取弹幕数量限制

        Returns:
            {'success': bool, 'data': {弹幕信息}} 或 {'success': False, 'error': str}
        """
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            # 检查凭据状态
            has_credential = self.credential is not None

            # 根据是否登录决定实际获取数量
            actual_limit = limit if has_credential else 100

            info = await v.get_info()
            duration = info.get("duration", 0)
            total_segments = (duration // 360) + 1

            all_danmaku_list = []
            segments_to_fetch = total_segments if has_credential else 1
            if segments_to_fetch > 10:
                segments_to_fetch = 10

            for i in range(segments_to_fetch):
                try:
                    danmaku_list = await v.get_danmakus(page_index=0, segment_index=i + 1)
                    all_danmaku_list.extend(danmaku_list)
                    if len(all_danmaku_list) >= actual_limit * 1.5:
                        break
                except Exception:
                    break

            if not all_danmaku_list:
                try:
                    all_danmaku_list = await v.get_danmakus(0)
                except Exception:
                    pass

            danmaku_texts = smart_sample_danmaku(all_danmaku_list, actual_limit)
            return {
                "success": True,
                "data": {
                    "danmaku_count": len(danmaku_texts),
                    "danmakus": danmaku_texts,
                    "full_text": "\n".join(danmaku_texts),
                    "has_credential": has_credential,
                },
            }
        except Exception as e:
            return {"success": False, "error": f"获取弹幕失败: {str(e)}"}

    async def get_comments(self, bvid: str, max_pages: int = 10, target_count: int = 100) -> Dict:
        """
        获取视频评论 (极致加固版：适配新版分页结构)

        Args:
            bvid: 视频BVID
            max_pages: 最大获取页数
            target_count: 目标评论数量

        Returns:
            {'success': bool, 'data': {评论信息}} 或 {'success': False, 'error': str}
        """
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            aid = info.get("aid")
            if not aid:
                return {"success": False, "error": "无法获取视频aid"}

            has_credential = self.credential is not None
            # 深度研究模式下不建议开启地毯式抓取，见好就收
            actual_max_pages = max_pages if has_credential else 3
            actual_target = target_count if has_credential else 50

            all_comments_list = []
            seen_rpids = set()

            # 抓取逻辑：优先尝试热门，不再暴力补全
            def get_next_offset(res):
                cursor = res.get("cursor", {})
                # 新版结构在 pagination_reply 内部
                if "pagination_reply" in cursor:
                    return cursor["pagination_reply"].get("next_offset", "")
                # 旧版可能直接在 cursor 下
                return cursor.get("next_offset", "")

            # --- 阶段 1：获取热门/置顶 ---
            try:
                # 热门模式 (Mode 3 通常代表热度排序)
                res_hot = await comment.get_comments_lazy(
                    aid,
                    comment.CommentResourceType.VIDEO,
                    order=comment.OrderType.LIKE,
                    credential=self.credential,
                )
                replies = res_hot.get("replies") or []
                # 包含置顶
                if res_hot.get("top", {}).get("reply"):
                    replies.insert(0, res_hot["top"]["reply"])

                for r in replies:
                    if r and r.get("rpid") not in seen_rpids:
                        seen_rpids.add(r.get("rpid"))
                        all_comments_list.append(r)

                # 如果热门还有下一页，多抓几页热门
                curr_pag = get_next_offset(res_hot)
                page_count = 1
                while (
                    curr_pag
                    and page_count < actual_max_pages
                    and len(all_comments_list) < actual_target
                ):
                    res_hot = await comment.get_comments_lazy(
                        aid,
                        comment.CommentResourceType.VIDEO,
                        offset=curr_pag,
                        order=comment.OrderType.LIKE,
                        credential=self.credential,
                    )
                    replies = res_hot.get("replies") or []
                    if not replies:
                        break
                    for r in replies:
                        if r and r.get("rpid") not in seen_rpids:
                            seen_rpids.add(r.get("rpid"))
                            all_comments_list.append(r)
                    curr_pag = get_next_offset(res_hot)
                    page_count += 1
            except Exception as e:
                logger.warning(f"抓取热门评论失败: {e}")

            # 采样与处理
            sampled_comments = all_comments_list[:actual_target]
            processed_comments = []
            for cmt in sampled_comments:
                member = cmt.get("member", {})
                content = cmt.get("content", {})
                processed_comments.append(
                    {
                        "username": member.get("uname", "未知用户"),
                        "message": content.get("message", ""),
                        "like": cmt.get("like", 0),
                        "reply_count": cmt.get("rcount", 0),
                        "time": cmt.get("ctime", 0),
                        "user_level": member.get("level_info", {}).get("current_level", 0),
                        "mid": member.get("mid", ""),
                        "avatar": member.get("avatar", ""),
                    }
                )

            logger.info(f"评论抓取完成: 实际获取 {len(processed_comments)} 条")

            return {
                "success": True,
                "data": {
                    "comments": processed_comments,
                    "total_count": len(all_comments_list),
                    "has_credential": has_credential,
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_stats(self, bvid: str) -> Dict:
        """
        获取视频统计信息

        Args:
            bvid: 视频BVID

        Returns:
            {'success': bool, 'data': {统计信息}} 或 {'success': False, 'error': str}
        """
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            stats = info.get("stat", {})
            online_info = None
            try:
                online = await v.get_online()
                online_info = {"total": online.get("total", 0), "web_count": online.get("count", 0)}
            except Exception:
                pass

            return {
                "success": True,
                "data": {
                    "view": stats.get("view", 0),
                    "like": stats.get("like", 0),
                    "coin": stats.get("coin", 0),
                    "favorite": stats.get("favorite", 0),
                    "share": stats.get("share", 0),
                    "danmaku": stats.get("danmaku", 0),
                    "reply": stats.get("reply", 0),
                    "online": online_info,
                },
            }
        except Exception as e:
            return {"success": False, "error": f"获取统计信息失败: {str(e)}"}

    async def get_related(self, bvid: str) -> Dict:
        """
        获取相关推荐视频

        Args:
            bvid: 视频BVID

        Returns:
            {'success': bool, 'data': [相关视频列表]} 或 {'success': False, 'error': str}
        """
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            related = await v.get_related()
            processed_related = []
            for item in related[:10]:
                processed_related.append(
                    {
                        "bvid": item.get("bvid"),
                        "title": item.get("title"),
                        "author": item.get("owner", {}).get("name"),
                        "cover": item.get("pic"),
                        "duration": item.get("duration"),
                        "duration_str": format_duration(item.get("duration", 0)),
                        "view": item.get("stat", {}).get("view", 0),
                    }
                )
            return {"success": True, "data": processed_related}
        except Exception as e:
            return {"success": False, "error": f"获取相关视频失败: {str(e)}"}

    async def get_cid(self, bvid: str) -> Optional[int]:
        """
        获取视频CID

        Args:
            bvid: 视频BVID

        Returns:
            CID，失败返回None
        """
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            return info.get("cid")
        except Exception:
            return None

    async def extract_frames(
        self, bvid: str, max_frames: Optional[int] = None, interval: Optional[int] = None
    ) -> Dict:
        """
        快速提取视频关键帧

        Args:
            bvid: 视频BVID
            max_frames: 最大帧数（可选）
            interval: 提取间隔（可选）

        Returns:
            {'success': bool, 'data': {帧信息}} 或 {'success': False, 'error': str}
        """
        try:

            async def fetch_image_as_jpeg_base64(url: str) -> Optional[str]:
                if not url:
                    return None
                if url.startswith("//"):
                    url = "https:" + url
                elif url.startswith("/"):
                    url = "https:" + url
                elif not url.startswith(("http://", "https://")):
                    url = "https://" + url

                headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com"}
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return None
                        img_bytes = await resp.read()

                nparr = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    return None
                ok, buffer = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 60])
                if not ok:
                    return None
                return base64.b64encode(buffer).decode("utf-8")

            cid = await self.get_cid(bvid)
            if not cid:
                return {"success": False, "error": "无法获取视频CID"}

            v_info = await self.get_info(bvid)
            video_data = v_info.get("data", {}) if v_info.get("success") else {}
            duration = video_data.get("duration", 600)
            cover_url = video_data.get("cover", "")

            api_url = f"https://api.bilibili.com/x/player/videoshot?bvid={bvid}&cid={cid}"
            headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com"}

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers) as resp:
                    data = await resp.json()

            if data.get("code") != 0 or "data" not in data:
                cover_frame = await fetch_image_as_jpeg_base64(cover_url)
                if cover_frame:
                    return {
                        "success": True,
                        "data": {
                            "frames": [cover_frame],
                            "frame_count": 1,
                            "video_duration": duration,
                            "source": "cover",
                        },
                    }
                return {"success": False, "error": "该视频不支持预览图且封面回退失败"}

            shot_data = data["data"]
            image_urls = shot_data.get("image", [])
            if not image_urls:
                cover_frame = await fetch_image_as_jpeg_base64(cover_url)
                if cover_frame:
                    return {
                        "success": True,
                        "data": {
                            "frames": [cover_frame],
                            "frame_count": 1,
                            "video_duration": duration,
                            "source": "cover",
                        },
                    }
                return {"success": False, "error": "未找到预览图数据且封面回退失败"}

            target_frames, _ = calculate_optimal_frame_params(duration)
            if max_frames:
                target_frames = max_frames

            frames_base64 = []
            count = 0
            async with aiohttp.ClientSession() as session:
                for img_url in image_urls[:2]:
                    if count >= target_frames:
                        break
                    if img_url.startswith("//"):
                        img_url = "https:" + img_url
                    async with session.get(img_url, headers=headers) as resp:
                        if resp.status != 200:
                            continue
                        img_bytes = await resp.read()

                    nparr = np.frombuffer(img_bytes, np.uint8)
                    sprite_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if sprite_img is None:
                        continue

                    s_h, s_w = sprite_img.shape[:2]
                    cols = 10
                    single_w = s_w // cols
                    single_h = s_h // 10
                    rows = s_h // single_h

                    for r in range(rows):
                        for c in range(cols):
                            if count >= target_frames:
                                break
                            if (r * cols + c) % 3 != 0:
                                continue
                            y, x = r * single_h, c * single_w
                            crop = sprite_img[y : y + single_h, x : x + single_w]
                            ok, buffer = cv2.imencode(".jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, 40])
                            if not ok:
                                continue
                            frames_base64.append(base64.b64encode(buffer).decode("utf-8"))
                            count += 1

            if not frames_base64:
                cover_frame = await fetch_image_as_jpeg_base64(cover_url)
                if cover_frame:
                    return {
                        "success": True,
                        "data": {
                            "frames": [cover_frame],
                            "frame_count": 1,
                            "video_duration": duration,
                            "source": "cover",
                        },
                    }
                return {"success": False, "error": "预览图切片失败且封面回退失败"}

            return {
                "success": True,
                "data": {
                    "frames": frames_base64,
                    "frame_count": len(frames_base64),
                    "video_duration": duration,
                    "source": "videoshot",
                },
            }
        except Exception as e:
            return {"success": False, "error": f"提取视频帧失败: {str(e)}"}

    async def get_video_tags(self, bvid: str) -> Dict:
        """
        获取视频标签及详细信息

        Args:
            bvid: 视频BVID

        Returns:
            {'success': bool, 'data': {标签列表}} 或 {'success': False, 'error': str}
        """
        try:

            v = video.Video(bvid=bvid, credential=self.credential)
            tags = await v.get_tags()

            # 获取每个标签的详细信息
            tag_details = []
            for tag in tags:
                tag_info = {
                    "tag_id": tag.get("tag_id"),
                    "tag_name": tag.get("tag_name"),
                    "jump_url": tag.get("jump_url"),
                    "is_activity": tag.get("is_activity", 0),
                    "type": tag.get("type"),
                }
                tag_details.append(tag_info)

            return {"success": True, "data": {"tags": tag_details, "tag_count": len(tag_details)}}
        except Exception as e:
            logger.error(f"获取视频标签失败: {str(e)}")
            return {"success": False, "error": f"获取视频标签失败: {str(e)}"}

    async def get_video_series(self, bvid: str) -> Dict:
        """
        获取视频所属的合集信息（系列视频）

        Args:
            bvid: 视频BVID

        Returns:
            {'success': bool, 'data': {合集信息}} 或 {'success': False, 'error': str}
        """
        try:
            v = video.Video(bvid=bvid, credential=self.credential)

            # 获取视频的合集信息
            series_list = await v.get_series()

            if not series_list or len(series_list) == 0:
                return {
                    "success": True,
                    "data": {"has_series": False, "message": "该视频不属于任何合集"},
                }

            # 获取第一个合集的详细信息
            series = series_list[0]
            series_id = series.get("sid")
            series_info = {
                "series_id": series_id,
                "series_title": series.get("title", ""),
                "series_cover": series.get("cover", ""),
                "total_videos": series.get("total", 0),
                "intro": series.get("intro", ""),
                "has_series": True,
            }

            # 尝试获取合集中的视频列表
            try:
                from bilibili_api import channel_series

                series_obj = channel_series.ChannelSeries(series_id=series_id)
                series_videos = await series_obj.get_videos()

                video_list = []
                for item in series_videos.get("list", [])[:20]:  # 限制返回前20个
                    video_list.append(
                        {
                            "bvid": item.get("bvid"),
                            "title": item.get("title"),
                            "index": item.get("index", 1),  # 集合中的序号
                        }
                    )

                series_info["videos"] = video_list
                series_info["video_count"] = len(video_list)

            except Exception as e:
                logger.warning(f"获取合集视频列表失败: {str(e)}")
                series_info["videos"] = []
                series_info["video_count"] = 0

            return {"success": True, "data": series_info}
        except Exception as e:
            logger.error(f"获取视频合集失败: {str(e)}")
            return {"success": False, "error": f"获取视频合集失败: {str(e)}"}

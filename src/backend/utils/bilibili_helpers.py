"""
B站工具方法模块
提供URL提取、格式化、智能采样等辅助功能
"""

import re
from typing import Dict, List, Optional


def format_duration(seconds: int) -> str:
    """
    格式化秒数为 时:分:秒

    Args:
        seconds: 秒数

    Returns:
        格式化的时长字符串，如 "1:23:45" 或 "12:34"
    """
    if not seconds:
        return "00:00"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def calculate_optimal_frame_params(duration_seconds: int) -> tuple[int, int]:
    """
    根据视频时长智能计算最优的帧提取参数

    Args:
        duration_seconds: 视频时长（秒）

    Returns:
        (max_frames, interval) - 最大帧数和提取间隔
    """
    if duration_seconds <= 120:
        max_frames = min(15, max(8, duration_seconds // 10))
        interval = max(5, duration_seconds // max_frames)
    elif duration_seconds <= 600:
        max_frames = 25
        interval = duration_seconds // max_frames
    elif duration_seconds <= 1800:
        max_frames = 40
        interval = duration_seconds // max_frames
    elif duration_seconds <= 3600:
        max_frames = 60
        interval = duration_seconds // max_frames
    else:
        max_frames = 80
        interval = max(60, duration_seconds // max_frames)

    max_frames = min(max_frames, 100)
    interval = max(5, interval)

    return max_frames, interval


def smart_sample_danmaku(danmaku_list: List, max_limit: int) -> List[str]:
    """
    智能采样弹幕

    根据弹幕总数和目标数量，智能均匀采样弹幕文本

    Args:
        danmaku_list: 弹幕对象列表
        max_limit: 最大采样数量

    Returns:
        采样后的弹幕文本列表
    """
    if not danmaku_list:
        return []

    total_count = len(danmaku_list)

    # 如果弹幕数量少于限制，全部返回
    if total_count <= max_limit:
        return [d.text for d in danmaku_list]

    # 否则均匀采样
    step = total_count / max_limit
    return [danmaku_list[int(i * step)].text for i in range(max_limit)]


def smart_sample_comments(comments_list: List, target_count: int) -> List:
    """
    智能采样评论

    根据评论总数和目标数量，智能均匀采样评论对象

    Args:
        comments_list: 评论对象列表
        target_count: 目标采样数量

    Returns:
        采样后的评论对象列表
    """
    if not comments_list:
        return []

    total_count = len(comments_list)

    # 如果评论数量少于目标，全部返回
    if total_count <= target_count:
        return comments_list

    # 否则均匀采样
    step = total_count / target_count
    return [comments_list[int(i * step)] for i in range(target_count)]


def extract_bvid(url: str) -> Optional[str]:
    """
    从B站链接中提取BVID

    支持多种B站URL格式：
    - 直接BVID: BV1xx411c7mD
    - 完整链接: https://www.bilibili.com/video/BV1xx411c7mD
    - 短链接: https://b23.tv/xxxxx

    Args:
        url: B站视频链接或BVID

    Returns:
        提取的BVID，失败返回None
    """
    patterns = [
        r"BV[a-zA-Z0-9]+",  # 直接BVID
        r"bilibili\.com/video/(BV[a-zA-Z0-9]+)",  # 完整链接
        r"b23\.tv/(\w+)",  # 短链接
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            bvid = match.group(1) if len(match.groups()) > 0 else match.group(0)
            if bvid.startswith("BV"):
                return bvid

    return None


def extract_article_id(url: str) -> Optional[Dict]:
    """
    从B站链接中提取专栏CV号或Opus动态号

    支持两种格式：
    - 传统专栏: cv12345 或 https://www.bilibili.com/read/cv12345
    - 新版Opus: https://www.bilibili.com/opus/123456

    Args:
        url: B站专栏或动态链接

    Returns:
        {'type': 'cv'/'opus', 'id': int}，失败返回None
    """
    # 传统专栏 CV
    cv_match = re.search(r"cv(\d+)|read/cv(\d+)", url)
    if cv_match:
        cvid = cv_match.group(1) or cv_match.group(2)
        return {"type": "cv", "id": int(cvid)}

    # 新版 Opus / 动态
    opus_match = re.search(r"opus/(\d+)|dynamic/(\d+)", url)
    if opus_match:
        oid = opus_match.group(1) or opus_match.group(2)
        return {"type": "opus", "id": int(oid)}

    return None


def get_next_offset_from_comment_response(res: Dict) -> str:
    """
    从评论响应中获取下一页偏移量

    兼容新旧版B站API的分页结构

    Args:
        res: API响应字典

    Returns:
        下一页偏移量，无则返回空字符串
    """
    cursor = res.get("cursor", {})

    # 新版结构在 pagination_reply 内部
    if "pagination_reply" in cursor:
        return cursor["pagination_reply"].get("next_offset", "")

    # 旧版可能直接在 cursor 下
    return cursor.get("next_offset", "")

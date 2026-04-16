"""
B站内容服务模块
提供专栏文章和Opus动态获取功能
"""

import re
from typing import Dict

from bilibili_api import article, dynamic

from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class ContentService:
    """
    B站内容服务类

    提供专栏和Opus相关的功能
    """

    def __init__(self, credential=None):
        """
        初始化内容服务

        Args:
            credential: B站登录凭据（可选）
        """
        self.credential = credential

    async def get_article_content(self, cvid: int) -> Dict:
        """
        获取专栏文章内容 (CV)

        Args:
            cvid: 专栏CV号

        Returns:
            {'success': bool, 'data': {文章信息}} 或 {'success': False, 'error': str}
        """
        try:
            art = article.Article(cvid, credential=self.credential)
            info = await art.get_info()

            # bilibili-api-python 新版本中，get_info() 不再返回 content，需要额外 fetch_content()
            clean_text = ""
            html_content = ""
            try:
                await art.fetch_content()
                children = getattr(art, "_Article__children", []) or []

                # ParagraphNode/TextNode 等提供 markdown()，直接拼接即可得到可读原文
                parts = []
                for node in children:
                    if hasattr(node, "markdown"):
                        try:
                            md = node.markdown()
                            if isinstance(md, str) and md.strip():
                                parts.append(md.strip())
                        except Exception:
                            continue
                clean_text = "\n\n".join(parts).strip()

                # meta 中通常带有 summary，可作为兜底
                if not clean_text:
                    meta = getattr(art, "_Article__meta", {}) or {}
                    summary = meta.get("summary") or ""
                    if isinstance(summary, str) and summary.strip():
                        clean_text = summary.strip()
            except Exception:
                # fetch_content 失败时，至少返回基本信息
                clean_text = ""

            return {
                "success": True,
                "data": {
                    "title": info.get("title"),
                    "author": info.get("author_name"),
                    "view": info.get("stats", {}).get("view"),
                    "like": info.get("stats", {}).get("like"),
                    "content": clean_text,
                    "html_content": html_content,
                    "banner_url": info.get("banner_url"),
                },
            }
        except Exception as e:
            return {"success": False, "error": f"获取专栏失败: {str(e)}"}

    async def get_opus_content(self, opus_id: int) -> Dict:
        """
        获取新版 Opus 动态/专栏内容 (加固版)

        Args:
            opus_id: Opus动态ID

        Returns:
            {'success': bool, 'data': {Opus信息}} 或 {'success': False, 'error': str}
        """
        try:
            dyn = dynamic.Dynamic(opus_id, credential=self.credential)
            raw_info = await dyn.get_info()

            # 兼容性处理：有时候返回带 item，有时候直接是内容
            info = raw_info.get("item", raw_info)
            modules = info.get("modules", {})
            module_dynamic = modules.get("module_dynamic", {})
            module_author = modules.get("module_author", {})

            # 提取作者
            author = module_author.get("name", "未知作者")
            face = module_author.get("face", "")

            # 提取正文
            content = ""
            title = "动态内容"

            major = module_dynamic.get("major", {})
            if major:
                # 专栏类型 (Opus)
                opus_data = major.get("opus", {})
                if opus_data:
                    title = opus_data.get("title", title)
                    # 优先取 summary.text，这通常是完整的或大部分内容
                    content = opus_data.get("summary", {}).get("text", "")

                    # 尝试从跳转链接中发现 CV 号，如果发现，可以考虑二次抓取
                    jump_url = opus_data.get("jump_url", "")
                    if "cv" in jump_url:
                        cv_id_match = re.search(r"cv(\d+)", jump_url)
                        if cv_id_match:
                            # 如果动态内容太短，尝试抓取原专栏
                            if len(content) < 500:
                                art_res = await self.get_article_content(int(cv_id_match.group(1)))
                                if art_res["success"]:
                                    return art_res

                # 图文类型
                draw_data = major.get("draw", {})
                if not content and draw_data:
                    items = draw_data.get("items", [])
                    content = "【图文动态】\n" + "\n".join(
                        [item.get("description", "") for item in items]
                    )

            # 备选方案：取动态描述
            if not content:
                desc = module_dynamic.get("desc", {})
                if desc:
                    content = desc.get("text", "")

            stat = modules.get("module_stat", {})

            return {
                "success": True,
                "data": {
                    "title": title,
                    "author": author,
                    "face": face,
                    "view": stat.get("view", {}).get("count", 0),
                    "like": stat.get("like", {}).get("count", 0),
                    "content": content,
                    "banner_url": (
                        major.get("draw", {}).get("items", [{}])[0].get("src", "")
                        if major.get("draw")
                        else ""
                    ),
                },
            }
        except Exception as e:
            import traceback

            traceback.print_exc()
            return {"success": False, "error": f"获取Opus内容失败: {str(e)}"}

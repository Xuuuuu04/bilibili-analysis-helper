"""
B站用户服务模块
提供用户信息、投稿视频等功能
"""

from typing import Dict

from bilibili_api import user

from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class UserService:
    """
    B站用户服务类

    提供用户相关的功能：信息获取、最近投稿等
    """

    def __init__(self, credential=None):
        """
        初始化用户服务

        Args:
            credential: B站登录凭据（可选）
        """
        self.credential = credential

    async def get_info(self, uid: int) -> Dict:
        """
        获取用户基本信息

        Args:
            uid: 用户UID

        Returns:
            {'success': bool, 'data': {用户信息}} 或 {'success': False, 'error': str}
        """
        try:
            u = user.User(uid=uid, credential=self.credential)
            info = await u.get_user_info()
            # 获取粉丝数等关系数据
            rel = await u.get_relation_info()
            return {
                "success": True,
                "data": {
                    "mid": info.get("mid"),
                    "name": info.get("name"),
                    "face": info.get("face"),
                    "sign": info.get("sign"),
                    "level": info.get("level"),
                    "follower": rel.get("follower", 0),
                    "official": info.get("official", {}).get("title"),
                },
            }
        except Exception as e:
            return {"success": False, "error": f"获取用户信息失败: {str(e)}"}

    async def get_recent_videos(self, uid: int, limit: int = 10) -> Dict:
        """
        获取用户最近投稿

        Args:
            uid: 用户UID
            limit: 获取视频数量

        Returns:
            {'success': bool, 'data': [视频列表]} 或 {'success': False, 'error': str}
        """
        try:
            u = user.User(uid=uid, credential=self.credential)
            # get_videos 返回的是一个生成器或者分页对象，通常直接调用拿到第一页
            # 注意：bilibili-api 的 user.get_videos 接口行为可能随版本变动，这里假设它返回标准结构
            res = await u.get_videos(ps=limit)
            v_list = res.get("list", {}).get("vlist", [])

            processed = []
            for v in v_list:
                processed.append(
                    {
                        "bvid": v.get("bvid"),
                        "title": v.get("title"),
                        "pic": v.get("pic"),
                        "play": v.get("play"),
                        "length": v.get("length"),
                    }
                )
            return {"success": True, "data": processed}
        except Exception as e:
            return {"success": False, "error": f"获取用户投稿失败: {str(e)}"}

    async def get_user_dynamics(self, uid: int, limit: int = 10) -> Dict:
        """
        获取用户的最新动态

        Args:
            uid: 用户UID
            limit: 获取动态数量

        Returns:
            {'success': bool, 'data': [动态列表]} 或 {'success': False, 'error': str}
        """
        try:
            from bilibili_api import dynamic

            # 获取用户动态页面
            dynamics_result = await dynamic.get_dynamic_page_info(
                type_=dynamic.DynamicType.ALL, offset=0, uid=uid
            )

            # 提取动态卡片列表
            cards = dynamics_result.get("cards", [])

            processed = []
            for card in cards[:limit]:
                # 动态卡片结构比较复杂，提取关键信息
                card_data = card.get("card", {})
                desc = card_data.get("desc", {})

                # 动态类型
                type_id = desc.get("type", 0)

                # 提取不同类型的内容
                content_text = ""
                if type_id == 2:  # 图文动态
                    item = card_data.get("item", {})
                    content_text = item.get("description", "")
                    # 提取图片
                    pictures = item.get("pictures", [])
                    pic_count = len(pictures)
                    if pic_count > 0:
                        content_text += f" [包含{pic_count}张图片]"

                elif type_id == 8:  # 视频动态
                    item = card_data.get("item", {})
                    content_text = f"分享了视频：{item.get('title', '')}"

                elif type_id == 4:  # 纯文本动态
                    item = card_data.get("item", {})
                    content_text = item.get("content", "")

                elif type_id == 64:  # 专栏动态
                    item = card_data.get("item", {})
                    content_text = f"发布了专栏：{item.get('title', '')}"

                # 提取互动数据
                stats = desc.get("stat", {})
                dynamic_info = {
                    "dynamic_id": desc.get("dynamic_id", ""),
                    "type": type_id,
                    "type_name": self._get_dynamic_type_name(type_id),
                    "content": content_text[:200]
                    + ("..." if len(content_text) > 200 else ""),  # 限制长度
                    "timestamp": desc.get("timestamp", 0),
                    "like": stats.get("liked", 0),
                    "reply": stats.get("reply", 0),
                    "repost": stats.get("repost", 0),
                }
                processed.append(dynamic_info)

            return {"success": True, "data": {"dynamics": processed, "total": len(processed)}}
        except Exception as e:
            logger.error(f"获取用户动态失败: {str(e)}")
            return {"success": False, "error": f"获取用户动态失败: {str(e)}"}

    @staticmethod
    def _get_dynamic_type_name(type_id: int) -> str:
        """获取动态类型名称"""
        type_map = {
            0: "未知",
            1: "转发",
            2: "图文",
            4: "纯文本",
            8: "视频",
            16: "短视频",
            64: "专栏",
            256: "音频",
        }
        return type_map.get(type_id, "其他")

"""
工具插件集合

所有具体的工具实现
"""

from .analyze_video import AnalyzeVideoTool
from .finish_research import FinishResearchTool
from .get_history_popular_videos import GetHistoryPopularVideosTool
from .get_hot_buzzwords import GetHotBuzzwordsTool
from .get_hot_search_keywords import GetHotSearchKeywordsTool
from .get_hot_videos import GetHotVideosTool
from .get_rank_videos import GetRankVideosTool
from .get_search_suggestions import GetSearchSuggestionsTool
from .get_user_dynamics import GetUserDynamicsTool
from .get_user_recent_videos import GetUserRecentVideosTool
from .get_video_series import GetVideoSeriesTool
from .get_video_tags import GetVideoTagsTool
from .get_weekly_hot_videos import GetWeeklyHotVideosTool
from .search_users import SearchUsersTool
from .search_videos import SearchVideosTool
from .web_search import WebSearchTool

__all__ = [
    "SearchVideosTool",
    "AnalyzeVideoTool",
    "WebSearchTool",
    "SearchUsersTool",
    "GetUserRecentVideosTool",
    "FinishResearchTool",
    "GetHotVideosTool",
    "GetHotBuzzwordsTool",
    "GetWeeklyHotVideosTool",
    "GetHistoryPopularVideosTool",
    "GetRankVideosTool",
    "GetSearchSuggestionsTool",
    "GetHotSearchKeywordsTool",
    "GetVideoTagsTool",
    "GetVideoSeriesTool",
    "GetUserDynamicsTool",
]

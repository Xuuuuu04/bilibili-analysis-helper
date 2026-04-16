"""
数据源专用异常模块

定义了数据源抽象层的所有异常类型，提供清晰的错误信息。
"""


class DataSourceError(Exception):
    """
    数据源基础异常类

    所有数据源相关异常的基类
    """

    def __init__(self, message: str, platform: str = None):
        """
        初始化异常

        Args:
            message: 错误信息
            platform: 平台名称（可选）
        """
        self.platform = platform
        self.message = message
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """格式化错误信息"""
        if self.platform:
            return f"[{self.platform}] {self.message}"
        return self.message


class UnsupportedPlatformError(DataSourceError):
    """
    不支持的平台异常

    当URL指定的平台不受支持时抛出
    """

    def __init__(self, url: str):
        """
        初始化异常

        Args:
            url: 不支持的URL
        """
        super().__init__(message=f"不支持的平台或URL: {url}", platform=None)
        self.url = url


class InvalidURLError(DataSourceError):
    """
    URL格式无效异常

    当URL格式不正确或无法解析时抛出
    """

    def __init__(self, url: str, reason: str = None, platform: str = None):
        """
        初始化异常

        Args:
            url: 无效的URL
            reason: 无效原因
            platform: 平台名称
        """
        message = f"无效的URL: {url}"
        if reason:
            message += f" ({reason})"

        super().__init__(message=message, platform=platform)
        self.url = url
        self.reason = reason


class VideoNotFoundError(DataSourceError):
    """
    视频不存在异常

    当视频ID无效或视频已被删除时抛出
    """

    def __init__(self, video_id: str, platform: str):
        """
        初始化异常

        Args:
            video_id: 视频ID
            platform: 平台名称
        """
        super().__init__(message=f"视频不存在或已被删除: {video_id}", platform=platform)
        self.video_id = video_id


class UserNotFoundError(DataSourceError):
    """
    用户不存在异常

    当用户ID无效或用户已被封禁时抛出
    """

    def __init__(self, user_id: str, platform: str):
        """
        初始化异常

        Args:
            user_id: 用户ID
            platform: 平台名称
        """
        super().__init__(message=f"用户不存在或已被封禁: {user_id}", platform=platform)
        self.user_id = user_id


class ArticleNotFoundError(DataSourceError):
    """
    文章不存在异常

    当文章ID无效或文章已被删除时抛出
    """

    def __init__(self, article_id: str, platform: str):
        """
        初始化异常

        Args:
            article_id: 文章ID
            platform: 平台名称
        """
        super().__init__(message=f"文章不存在或已被删除: {article_id}", platform=platform)
        self.article_id = article_id


class APIError(DataSourceError):
    """
    API调用失败异常

    当平台API调用失败时抛出
    """

    def __init__(
        self, message: str, platform: str, status_code: int = None, response_data: dict = None
    ):
        """
        初始化异常

        Args:
            message: 错误信息
            platform: 平台名称
            status_code: HTTP状态码（可选）
            response_data: 响应数据（可选）
        """
        full_message = f"API调用失败: {message}"
        if status_code:
            full_message += f" (HTTP {status_code})"

        super().__init__(message=full_message, platform=platform)
        self.status_code = status_code
        self.response_data = response_data


class AuthenticationError(DataSourceError):
    """
    认证失败异常

    当登录凭据无效或过期时抛出
    """

    def __init__(self, platform: str, reason: str = None):
        """
        初始化异常

        Args:
            platform: 平台名称
            reason: 失败原因
        """
        message = "认证失败"
        if reason:
            message += f": {reason}"

        super().__init__(message=message, platform=platform)
        self.reason = reason


class RateLimitError(DataSourceError):
    """
    请求频率限制异常

    当触发平台API频率限制时抛出
    """

    def __init__(self, platform: str, retry_after: int = None, limit: int = None):
        """
        初始化异常

        Args:
            platform: 平台名称
            retry_after: 重试等待时间（秒）
            limit: 限制次数
        """
        message = "触发API频率限制"
        if retry_after:
            message += f"，请在 {retry_after} 秒后重试"
        if limit:
            message += f"（限制: {limit} 次）"

        super().__init__(message=message, platform=platform)
        self.retry_after = retry_after
        self.limit = limit


class FeatureNotSupportedError(DataSourceError):
    """
    功能不支持异常

    当平台不支持某功能时抛出（如弹幕）
    """

    def __init__(self, platform: str, feature: str):
        """
        初始化异常

        Args:
            platform: 平台名称
            feature: 功能名称
        """
        super().__init__(message=f"该平台不支持 '{feature}' 功能", platform=platform)
        self.feature = feature


class ContentAccessDeniedError(DataSourceError):
    """
    内容访问拒绝异常

    当内容需要付费、会员或地区限制时抛出
    """

    def __init__(self, platform: str, content_id: str, reason: str = None):
        """
        初始化异常

        Args:
            platform: 平台名称
            content_id: 内容ID
            reason: 拒绝原因
        """
        message = f"无法访问内容: {content_id}"
        if reason:
            message += f" ({reason})"
        else:
            message += " (可能需要付费、会员或受地区限制)"

        super().__init__(message=message, platform=platform)
        self.content_id = content_id
        self.reason = reason


class CredentialRequiredError(DataSourceError):
    """
    需要登录凭据异常

    当访问需要登录的内容但未提供凭据时抛出
    """

    def __init__(self, platform: str, resource: str = None):
        """
        初始化异常

        Args:
            platform: 平台名称
            resource: 资源描述
        """
        message = "需要登录凭据才能访问"
        if resource:
            message += f" {resource}"

        super().__init__(message=message, platform=platform)
        self.resource = resource


class InvalidParameterError(DataSourceError):
    """
    参数无效异常

    当传递的参数不符合要求时抛出
    """

    def __init__(self, platform: str, parameter: str, reason: str = None):
        """
        初始化异常

        Args:
            platform: 平台名称
            parameter: 参数名
            reason: 无效原因
        """
        message = f"参数 '{parameter}' 无效"
        if reason:
            message += f": {reason}"

        super().__init__(message=message, platform=platform)
        self.parameter = parameter
        self.reason = reason


class NetworkError(DataSourceError):
    """
    网络错误异常

    当网络请求失败时抛出
    """

    def __init__(self, platform: str, url: str = None, reason: str = None):
        """
        初始化异常

        Args:
            platform: 平台名称
            url: 请求URL
            reason: 失败原因
        """
        message = "网络请求失败"
        if url:
            message += f" ({url})"
        if reason:
            message += f": {reason}"

        super().__init__(message=message, platform=platform)
        self.url = url
        self.reason = reason


class ParseError(DataSourceError):
    """
    数据解析错误异常

    当解析平台返回的数据失败时抛出
    """

    def __init__(self, platform: str, data_type: str, reason: str = None):
        """
        初始化异常

        Args:
            platform: 平台名称
            data_type: 数据类型
            reason: 失败原因
        """
        message = f"解析{data_type}失败"
        if reason:
            message += f": {reason}"

        super().__init__(message=message, platform=platform)
        self.data_type = data_type
        self.reason = reason

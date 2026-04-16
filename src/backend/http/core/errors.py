"""
================================================================================
异常定义模块 (src/backend/http/core/errors.py)
================================================================================

【架构位置】
位于 HTTP 层的核心模块，定义应用的所有异常类型。

【设计模式】
- 数据类模式（@dataclass）：简化类的定义
- 继承层次：基类 + 三个具体异常类

【主要功能】
1. 定义统一的异常基类
2. 提供三种常用异常类型
3. 自动格式化错误消息

【异常类型】
- BadRequestError (400): 请求参数错误
- NotFoundError (404): 资源不存在
- UpstreamError (502): 上游服务错误

================================================================================
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AppError(Exception):
    """
    应用异常基类（不可变数据类）

    设计模式：数据类模式 + 继承
    - frozen=True：创建后不可修改，确保异常信息的一致性
    - 继承 Exception：可以被 raise 和 except 捕获

    Attributes:
        message: 错误消息
        status_code: HTTP 状态码（默认 400）

    使用示例：
        raise AppError("发生错误", status_code=500)
    """

    message: str
    status_code: int = 400

    def __str__(self) -> str:
        """返回错误消息"""
        return self.message


class BadRequestError(AppError):
    """请求参数错误（400）"""

    def __init__(self, message: str):
        super().__init__(message=message, status_code=400)


class NotFoundError(AppError):
    """资源不存在（404）"""

    def __init__(self, message: str):
        super().__init__(message=message, status_code=404)


class UpstreamError(AppError):
    """上游服务错误（502）"""

    def __init__(self, message: str):
        super().__init__(message=message, status_code=502)

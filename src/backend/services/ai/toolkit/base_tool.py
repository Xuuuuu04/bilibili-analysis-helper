"""
BaseTool - 工具基类模块

定义所有工具插件的抽象接口和基础功能
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator


class BaseTool(ABC):
    """
    工具基类

    所有工具插件必须继承此类并实现抽象方法。
    提供统一的工具接口、参数验证和错误处理机制。
    """

    def __init__(self):
        """初始化工具"""
        self._bilibili_service = None
        self._client = None
        self._model = None

    @property
    @abstractmethod
    def name(self) -> str:
        """
        工具名称

        Returns:
            str: 工具的唯一标识符
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        工具描述

        用于AI模型理解工具的功能和使用场景。

        Returns:
            str: 工具的功能描述
        """
        pass

    @property
    def schema(self) -> Dict:
        """
        工具参数Schema（JSON Schema格式）

        定义工具的输入参数结构，用于OpenAI Function Calling。

        Returns:
            Dict: JSON Schema格式的参数定义
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        }

    @abstractmethod
    async def execute(self, **kwargs) -> Dict:
        """
        执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            Dict: 执行结果，格式:
                {
                    'type': 'tool_result' | 'error',
                    'tool': str,
                    'data': Any,
                    'error': str (仅错误时)
                }
        """
        pass

    def validate_args(self, args: Dict) -> bool:
        """
        验证参数

        默认实现验证所有必需参数是否存在。
        子类可以重写此方法以实现自定义验证逻辑。

        Args:
            args: 待验证的参数字典

        Returns:
            bool: 参数是否有效
        """
        schema_params = self.schema.get("function", {}).get("parameters", {})
        required = schema_params.get("required", [])

        for param in required:
            if param not in args:
                return False

        return True

    def set_bilibili_service(self, service):
        """
        设置B站服务实例

        Args:
            service: BilibiliService实例
        """
        self._bilibili_service = service

    def set_ai_client(self, client, model: str = None):
        """
        设置AI客户端和模型

        Args:
            client: OpenAI客户端实例
            model: 模型名称（可选）
        """
        self._client = client
        self._model = model

    def to_json_result(self, data: Any, success: bool = True) -> str:
        """
        将结果转换为JSON字符串

        Args:
            data: 要序列化的数据
            success: 是否成功

        Returns:
            str: JSON字符串
        """
        return json.dumps(data, ensure_ascii=False)

    def __repr__(self) -> str:
        """工具的字符串表示"""
        return f"<{self.__class__.__name__}: {self.name}>"


class StreamableTool(BaseTool):
    """
    可流式输出的工具基类

    用于需要逐步返回执行进度的工具（如视频分析）。
    """

    @abstractmethod
    async def execute_stream(self, **kwargs) -> Generator[Dict, None, None]:
        """
        流式执行工具

        Args:
            **kwargs: 工具参数

        Yields:
            Dict: 执行进度和结果，格式:
                {
                    'type': 'tool_progress' | 'tool_result' | 'error',
                    'tool': str,
                    'data': Any,
                    'message': str,
                    'error': str (仅错误时)
                }
        """
        pass

    async def execute(self, **kwargs) -> Dict:
        """
        默认执行方法（非流式）

        子类应实现 execute_stream，execute 默认收集所有流式结果后返回。
        """
        results = []
        async for item in self.execute_stream(**kwargs):
            results.append(item)

        return {"type": "tool_result", "tool": self.name, "data": results}

"""
ToolRegistry - 工具注册中心

提供工具的注册、注销、查询和执行功能
"""

from typing import Dict, List, Optional, Type

from src.backend.utils.logger import get_logger

from .base_tool import BaseTool

logger = get_logger(__name__)


class ToolRegistry:
    """
    工具注册中心

    单例模式，管理所有工具插件的注册、查找和执行。
    所有方法为 @classmethod，状态存储在类属性 _tools/_tool_categories 中。
    """

    _tools: Dict[str, BaseTool] = {}
    _tool_categories: Dict[str, List[str]] = {}
    _instance = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def _ensure_initialized(cls):
        """确保类属性已初始化（防止被 clear 后 defaultdict 行为丢失）"""
        if not isinstance(cls._tools, dict):
            cls._tools = {}
        if not isinstance(cls._tool_categories, dict):
            cls._tool_categories = {}

    @classmethod
    def register(cls, tool: BaseTool, category: str = "default") -> None:
        """
        注册工具

        Args:
            tool: 工具实例
            category: 工具分类（可选）

        Raises:
            ValueError: 如果工具名称已存在
        """
        cls._ensure_initialized()
        name = tool.name

        if name in cls._tools:
            logger.warning(f"工具 '{name}' 已存在，将被覆盖")
            # 从旧分类中清除
            for cat_tools in cls._tool_categories.values():
                if name in cat_tools:
                    cat_tools.remove(name)

        cls._tools[name] = tool
        if category not in cls._tool_categories:
            cls._tool_categories[category] = []
        if name not in cls._tool_categories[category]:
            cls._tool_categories[category].append(name)

        logger.info(f"注册工具: {name} (分类: {category})")

    @classmethod
    def register_class(cls, tool_class: Type[BaseTool], category: str = "default") -> None:
        """
        通过类注册工具（自动实例化）

        Args:
            tool_class: 工具类
            category: 工具分类（可选）
        """
        tool_instance = tool_class()
        cls.register(tool_instance, category)

    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        注销工具

        Args:
            name: 工具名称

        Returns:
            bool: 是否成功注销
        """
        if name in cls._tools:
            del cls._tools[name]

            # 从分类中移除
            for _category, tools in cls._tool_categories.items():
                if name in tools:
                    tools.remove(name)

            logger.info(f"注销工具: {name}")
            return True

        logger.warning(f"尝试注销不存在的工具: {name}")
        return False

    @classmethod
    def get_tool(cls, name: str) -> Optional[BaseTool]:
        """
        获取工具实例

        Args:
            name: 工具名称

        Returns:
            BaseTool: 工具实例，如果不存在则返回 None
        """
        return cls._tools.get(name)

    @classmethod
    def has_tool(cls, name: str) -> bool:
        """
        检查工具是否存在

        Args:
            name: 工具名称

        Returns:
            bool: 工具是否存在
        """
        return name in cls._tools

    @classmethod
    def list_tools(cls, category: str = None) -> List[str]:
        """
        列出所有工具名称

        Args:
            category: 分类筛选（可选）

        Returns:
            List[str]: 工具名称列表
        """
        if category:
            return cls._tool_categories.get(category, []).copy()

        return list(cls._tools.keys())

    @classmethod
    def list_tools_schema(cls, category: str = None) -> List[Dict]:
        """
        列出所有工具的Schema

        用于OpenAI Function Calling的tools参数。

        Args:
            category: 分类筛选（可选）

        Returns:
            List[Dict]: 工具Schema列表
        """
        if category:
            tool_names = cls._tool_categories.get(category, [])
        else:
            tool_names = cls._tools.keys()

        return [cls._tools[name].schema for name in tool_names if name in cls._tools]

    @classmethod
    def get_tool_info(cls, name: str) -> Optional[Dict]:
        """
        获取工具详细信息

        Args:
            name: 工具名称

        Returns:
            Dict: 工具信息，如果不存在则返回 None
        """
        tool = cls.get_tool(name)
        if not tool:
            return None

        return {
            "name": tool.name,
            "description": tool.description,
            "schema": tool.schema,
            "class": tool.__class__.__name__,
            "module": tool.__class__.__module__,
        }

    @classmethod
    def clear(cls, category: str = None) -> None:
        """
        清空工具

        Args:
            category: 分类筛选（可选），如果指定则只清空该分类
        """
        if category:
            tool_names = cls._tool_categories.get(category, []).copy()
            for name in tool_names:
                cls.unregister(name)
        else:
            cls._tools = {}
            cls._tool_categories = {}

        logger.info(f"清空工具: {category if category else '全部'}")

    @classmethod
    def count(cls) -> int:
        """
        获取工具总数

        Returns:
            int: 工具数量
        """
        return len(cls._tools)

    @classmethod
    async def execute_tool(cls, name: str, **kwargs) -> Dict:
        """
        执行工具

        Args:
            name: 工具名称
            **kwargs: 工具参数

        Returns:
            Dict: 执行结果

        Raises:
            ValueError: 如果工具不存在
        """
        tool = cls.get_tool(name)
        if not tool:
            raise ValueError(f"工具 '{name}' 不存在")

        # 验证参数
        if not tool.validate_args(kwargs):
            missing_params = []
            schema_params = tool.schema.get("function", {}).get("parameters", {})
            required = schema_params.get("required", [])
            for param in required:
                if param not in kwargs:
                    missing_params.append(param)

            raise ValueError(f"参数验证失败，缺少必需参数: {', '.join(missing_params)}")

        # 执行工具
        try:
            result = await tool.execute(**kwargs)
            return result
        except Exception as e:
            logger.error(f"执行工具 '{name}' 失败: {str(e)}")
            return {"type": "error", "tool": name, "error": str(e)}

    @classmethod
    def set_services(cls, bilibili_service=None, ai_client=None, model: str = None):
        """
        为所有工具设置服务依赖

        Args:
            bilibili_service: B站服务实例
            ai_client: AI客户端实例
            model: 模型名称
        """
        for tool in cls._tools.values():
            if bilibili_service:
                tool.set_bilibili_service(bilibili_service)
            if ai_client:
                tool.set_ai_client(ai_client, model)

        logger.info(f"已为 {cls.count()} 个工具设置服务依赖")


def register_tool(name: str = None, category: str = "default"):
    """
    工具注册装饰器

    用法:
        @register_tool(category="bilibili")
        class MyTool(BaseTool):
            ...

    Args:
        name: 工具名称（可选，默认使用类名）
        category: 工具分类（可选）
    """

    def decorator(cls):
        # 实例化工具
        tool_instance = cls()

        # 如果指定了名称，重写工具的name属性
        if name:
            # 注意：这里假设子类通过属性定义name，
            # 如果是@property，需要特殊处理
            # 简单起见，我们通过monkey patching设置
            tool_instance._custom_name = name

            # 重写name属性
            type(tool_instance).name = property(lambda self: name)

        # 注册工具
        ToolRegistry.register(tool_instance, category)

        return cls

    return decorator


# 便捷函数
def get_registry() -> ToolRegistry:
    """获取注册中心实例"""
    return ToolRegistry()

from typing import Dict, List, Optional

from src.backend.utils.logger import get_logger

from .base_tool import BaseTool

logger = get_logger(__name__)


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_categories: Dict[str, List[str]] = {}

    def register(self, tool: BaseTool, category: str = "default") -> None:
        name = tool.name
        if name in self._tools:
            logger.warning(f"工具 '{name}' 已存在，将被覆盖")
            for cat_tools in self._tool_categories.values():
                if name in cat_tools:
                    cat_tools.remove(name)
        self._tools[name] = tool
        if category not in self._tool_categories:
            self._tool_categories[category] = []
        if name not in self._tool_categories[category]:
            self._tool_categories[category].append(name)

    def unregister(self, name: str) -> None:
        if name in self._tools:
            del self._tools[name]
            for cat_tools in self._tool_categories.values():
                if name in cat_tools:
                    cat_tools.remove(name)

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def get_all(self) -> Dict[str, BaseTool]:
        return dict(self._tools)

    def get_by_category(self, category: str) -> List[BaseTool]:
        tool_names = self._tool_categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def clear(self) -> None:
        self._tools.clear()
        self._tool_categories.clear()

    async def execute(self, name: str, **kwargs):
        tool = self.get(name)
        if not tool:
            raise ValueError(f"工具 '{name}' 未注册")
        return await tool.execute(**kwargs)

    def get_openai_tools(self) -> List[Dict]:
        return [tool.schema for tool in self._tools.values()]

    def get_tool_definitions(self) -> List[Dict]:
        definitions = []
        for name, tool in self._tools.items():
            categories = [
                cat for cat, tools in self._tool_categories.items() if name in tools
            ]
            definitions.append({
                "name": name,
                "category": categories[0] if categories else "default",
                "description": tool.description,
            })
        return definitions


def register_tool(name: str = None, category: str = "default"):
    def decorator(cls):
        tool_instance = cls()
        if name:
            tool_instance._custom_name = name
            type(tool_instance).name = property(lambda self: name)
        _default_registry.register(tool_instance, category)
        return cls

    return decorator


_default_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    return _default_registry

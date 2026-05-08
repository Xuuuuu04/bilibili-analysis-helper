import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backend.services.ai.toolkit.base_tool import BaseTool
from src.backend.services.ai.toolkit.tool_registry import ToolRegistry


class MockTool(BaseTool):
    def __init__(self, name: str, description: str = "mock tool", category: str = "default"):
        self._name = name
        self._description = description
        super().__init__()

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    async def execute(self, **kwargs):
        return {"type": "tool_result", "tool": self.name, "data": kwargs}


def test_register_and_get():
    registry = ToolRegistry()
    tool = MockTool("test_tool")
    registry.register(tool)
    assert registry.get("test_tool") is tool


def test_register_duplicate_overwrites():
    registry = ToolRegistry()
    tool1 = MockTool("dup_tool", description="first")
    tool2 = MockTool("dup_tool", description="second")
    registry.register(tool1, category="cat_a")
    registry.register(tool2, category="cat_b")
    assert registry.get("dup_tool") is tool2
    assert registry.get_by_category("cat_a") == []
    assert registry.get_by_category("cat_b") == [tool2]


def test_unregister():
    registry = ToolRegistry()
    tool = MockTool("removable")
    registry.register(tool, category="cat")
    assert registry.get("removable") is tool
    registry.unregister("removable")
    assert registry.get("removable") is None
    assert registry.get_by_category("cat") == []


def test_get_nonexistent():
    registry = ToolRegistry()
    assert registry.get("no_such_tool") is None


def test_get_all():
    registry = ToolRegistry()
    t1 = MockTool("a")
    t2 = MockTool("b")
    registry.register(t1)
    registry.register(t2)
    all_tools = registry.get_all()
    assert len(all_tools) == 2
    assert all_tools["a"] is t1
    assert all_tools["b"] is t2


def test_get_by_category():
    registry = ToolRegistry()
    t1 = MockTool("x")
    t2 = MockTool("y")
    t3 = MockTool("z")
    registry.register(t1, category="alpha")
    registry.register(t2, category="beta")
    registry.register(t3, category="alpha")
    alpha = registry.get_by_category("alpha")
    beta = registry.get_by_category("beta")
    assert len(alpha) == 2
    assert t1 in alpha
    assert t3 in alpha
    assert beta == [t2]
    assert registry.get_by_category("gamma") == []


def test_clear():
    registry = ToolRegistry()
    registry.register(MockTool("p"))
    registry.register(MockTool("q"), category="cat")
    registry.clear()
    assert registry.get_all() == {}
    assert registry.get_by_category("cat") == []


@pytest.mark.asyncio
async def test_execute_calls_tool():
    registry = ToolRegistry()
    tool = MockTool("exec_tool")
    tool.execute = AsyncMock(return_value={"type": "tool_result", "tool": "exec_tool", "data": {"ok": True}})
    registry.register(tool)
    result = await registry.execute("exec_tool", key="val")
    tool.execute.assert_awaited_once_with(key="val")
    assert result == {"type": "tool_result", "tool": "exec_tool", "data": {"ok": True}}


@pytest.mark.asyncio
async def test_execute_nonexistent_raises():
    registry = ToolRegistry()
    with pytest.raises(ValueError, match="未注册"):
        await registry.execute("ghost_tool")


def test_get_openai_tools():
    registry = ToolRegistry()
    t1 = MockTool("o1", description="first")
    t2 = MockTool("o2", description="second")
    registry.register(t1)
    registry.register(t2)
    schemas = registry.get_openai_tools()
    assert len(schemas) == 2
    names = {s["function"]["name"] for s in schemas}
    assert names == {"o1", "o2"}
    for s in schemas:
        assert s["type"] == "function"
        assert "parameters" in s["function"]


def test_instance_isolation():
    r1 = ToolRegistry()
    r2 = ToolRegistry()
    t1 = MockTool("only_in_r1")
    t2 = MockTool("only_in_r2")
    r1.register(t1)
    r2.register(t2)
    assert r1.get("only_in_r1") is t1
    assert r1.get("only_in_r2") is None
    assert r2.get("only_in_r2") is t2
    assert r2.get("only_in_r1") is None

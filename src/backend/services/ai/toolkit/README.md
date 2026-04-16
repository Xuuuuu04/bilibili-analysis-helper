# Toolkit - 工具插件系统快速参考

## 目录结构

```
toolkit/
├── __init__.py           # 模块导出
├── base_tool.py          # BaseTool 和 StreamableTool 基类
├── tool_registry.py      # ToolRegistry 注册中心
└── tools/                # 工具插件目录
    ├── __init__.py
    ├── search_videos.py
    ├── analyze_video.py
    ├── web_search.py
    ├── search_users.py
    ├── get_user_recent_videos.py
    └── finish_research.py
```

## 快速开始

### 1. 导入注册中心

```python
from src.backend.services.ai.toolkit import ToolRegistry
```

### 2. 注册工具

```python
from src.backend.services.ai.toolkit.tools import SearchVideosTool

# 方式1: 直接注册
tool = SearchVideosTool()
ToolRegistry.register(tool)

# 方式2: 使用装饰器（需要先导入）
from src.backend.services.ai.toolkit import register_tool

@register_tool(category="bilibili")
class MyCustomTool(BaseTool):
    pass
```

### 3. 使用工具

```python
# 获取工具
tool = ToolRegistry.get_tool('search_videos')

# 设置服务依赖
tool.set_bilibili_service(bilibili_service)
tool.set_ai_client(client, model)

# 执行工具
result = await tool.execute(keyword="Python教程")
```

### 4. 获取所有工具Schema

```python
schemas = ToolRegistry.list_tools_schema()
# 用于 OpenAI Function Calling
```

## 创建新工具

### 普通工具

```python
from typing import Dict
from src.backend.services.ai.toolkit import BaseTool

class MyTool(BaseTool):
    """我的工具"""

    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "工具功能描述"

    @property
    def schema(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {
                            "type": "string",
                            "description": "参数1"
                        }
                    },
                    "required": ["param1"]
                }
            }
        }

    async def execute(self, param1: str) -> Dict:
        """执行工具逻辑"""
        try:
            # 你的逻辑
            result = do_something(param1)

            return {
                'type': 'tool_result',
                'tool': self.name,
                'data': result
            }
        except Exception as e:
            return {
                'type': 'error',
                'tool': self.name,
                'error': str(e)
            }
```

### 流式工具

```python
from typing import Dict, Generator
from src.backend.services.ai.toolkit import StreamableTool

class MyStreamTool(StreamableTool):
    """流式输出工具"""

    @property
    def name(self) -> str:
        return "my_stream_tool"

    @property
    def description(self) -> str:
        return "流式工具描述"

    async def execute_stream(self, param1: str) -> Generator[Dict, None, None]:
        """流式执行"""

        # 发送进度
        yield {
            'type': 'tool_progress',
            'tool': self.name,
            'message': '处理中...'
        }

        # 处理逻辑
        result = process_long_task(param1)

        # 发送结果
        yield {
            'type': 'tool_result',
            'tool': self.name,
            'data': result
        }
```

## ToolRegistry API

### 类方法

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `register(tool, category)` | 注册工具 | None |
| `unregister(name)` | 注销工具 | bool |
| `get_tool(name)` | 获取工具实例 | BaseTool |
| `has_tool(name)` | 检查工具是否存在 | bool |
| `list_tools(category)` | 列出工具名称 | List[str] |
| `list_tools_schema(category)` | 列出工具Schema | List[Dict] |
| `get_tool_info(name)` | 获取工具详细信息 | Dict |
| `clear(category)` | 清空工具 | None |
| `count()` | 获取工具总数 | int |
| `set_services(...)` | 设置服务依赖 | None |
| `execute_tool(name, **kwargs)` | 执行工具 | Dict |

### 使用示例

```python
# 查询工具
if ToolRegistry.has_tool('search_videos'):
    tool = ToolRegistry.get_tool('search_videos')
    print(tool.description)

# 列出所有工具
tools = ToolRegistry.list_tools()
print(f"可用工具: {', '.join(tools)}")

# 按分类列出工具
bilibili_tools = ToolRegistry.list_tools(category='bilibili')

# 获取Schema
schemas = ToolRegistry.list_tools_schema()

# 执行工具
result = await ToolRegistry.execute_tool('search_videos', keyword='Python')

# 清空所有工具
ToolRegistry.clear()
```

## 工具返回格式

### 成功结果

```python
{
    'type': 'tool_result',
    'tool': 'tool_name',
    'data': {...}  # 任意数据
}
```

### 错误结果

```python
{
    'type': 'error',
    'tool': 'tool_name',
    'error': '错误信息'
}
```

### 流式进度

```python
{
    'type': 'tool_progress',
    'tool': 'tool_name',
    'message': '处理中...',  # 可选
    'data': {...}  # 可选
}
```

## 在 Agent 中使用

```python
from src.backend.services.ai.toolkit import ToolRegistry
from src.backend.services.ai.toolkit.tools import SearchVideosTool

class MyAgent:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self._initialize_tools()

    def _initialize_tools(self):
        """初始化工具"""
        ToolRegistry.clear()

        # 注册工具
        tools = [SearchVideosTool(), ...]
        for tool in tools:
            ToolRegistry.register(tool)
            tool.set_ai_client(self.client, self.model)

    def stream_chat(self, question, bilibili_service):
        # 设置服务依赖
        ToolRegistry.set_services(bilibili_service=bilibili_service)

        # 获取工具Schema
        tools_schema = ToolRegistry.list_tools_schema()

        # 调用 OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[...],
            tools=tools_schema
        )

        # 处理工具调用
        for tool_call in response.tool_calls:
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            # 执行工具
            result = await ToolRegistry.execute_tool(func_name, **args)
```

## 注意事项

1. **异步执行**: 所有工具的 `execute` 方法都是异步的
2. **参数验证**: 使用 `validate_args()` 方法验证参数
3. **服务依赖**: 使用前需要设置 `bilibili_service` 和 `ai_client`
4. **错误处理**: 工具应该捕获异常并返回错误格式
5. **日志记录**: 使用 `logger` 记录重要操作

## 调试技巧

```python
# 查看所有已注册工具
print(f"已注册工具: {ToolRegistry.list_tools()}")

# 查看工具信息
info = ToolRegistry.get_tool_info('search_videos')
print(f"工具信息: {info}")

# 测试参数验证
tool = ToolRegistry.get_tool('search_videos')
is_valid = tool.validate_args({'keyword': 'test'})
print(f"参数有效: {is_valid}")
```
